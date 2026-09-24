// Site-server connection (technical spec §6.1–§6.2, T22 app part): pairing, bootstrap, and the push/pull loop.
// Signing, wire mapping and verdict handling live in @shiftmate/core (pure); this file does the network I/O.
import {
  API_PREFIX, type BootstrapResponse, type LedgerEntry, type LedgerStore, type PushResult, type ServerChange,
  applyPushResults, pendingForPush, pullPath, pushBody, signedHeaders,
} from '@shiftmate/core';
import { create } from 'zustand';

export interface Pairing {
  baseUrl: string;
  deviceId: string;
  secret: string;
  machineId: string;
  cursor: number;
}

export interface SyncState {
  mode: 'local' | 'server';
  baseUrl: string | null;
  online: boolean | null;       // null = not tried yet
  simulatedOffline: boolean;    // presenter "Simulate no signal"
  lastSyncAt: number | null;
  lastError: string | null;
  rejected: string[];
  changesApplied: number;
}

export const useSync = create<SyncState>(() => ({
  mode: 'local', baseUrl: null, online: null, simulatedOffline: false, lastSyncAt: null, lastError: null, rejected: [],
  changesApplied: 0,
}));

const PAIRING_KEY = 'shiftmate.pairing';
const LAST_URL_KEY = 'shiftmate.server_url';
const CLIENT_ID_KEY = 'shiftmate.client_device_id';
const REQUEST_TIMEOUT_MS = 8000;
export const SYNC_INTERVAL_MS = 5000;

// Web keeps the pairing in localStorage; native Expo Go keeps it for the session (re-pairing is allowed in demo mode).
const memory = new Map<string, string>();
function getItem(key: string): string | null {
  try {
    return globalThis.localStorage?.getItem(key) ?? memory.get(key) ?? null;
  } catch {
    return memory.get(key) ?? null;
  }
}
function setItem(key: string, value: string | null): void {
  if (value === null) memory.delete(key);
  else memory.set(key, value);
  try {
    if (value === null) globalThis.localStorage?.removeItem(key);
    else globalThis.localStorage?.setItem(key, value);
  } catch {
    // storage unavailable: memory copy only
  }
}

export function loadPairing(): Pairing | null {
  const raw = getItem(PAIRING_KEY);
  try {
    return raw ? (JSON.parse(raw) as Pairing) : null;
  } catch {
    return null;
  }
}
export function savePairing(p: Pairing | null): void {
  setItem(PAIRING_KEY, p ? JSON.stringify(p) : null);
  if (p) setItem(LAST_URL_KEY, p.baseUrl);
}
export function lastServerUrl(): string {
  return getItem(LAST_URL_KEY) ?? process.env.EXPO_PUBLIC_DEFAULT_SERVER_URL ?? '';
}
export function clientDeviceId(newId: () => string): string {
  const existing = getItem(CLIENT_ID_KEY);
  if (existing) return existing;
  const id = newId();
  setItem(CLIENT_ID_KEY, id);
  return id;
}

// Private-network hosts: the site server speaks plain HTTP on the LAN (spec §13.4 "HTTP on LAN")
const LAN_HOST = /^(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/;

/** "192.168.1.10:8000", "http://…/", "http://…/api/v1" → "http://192.168.1.10:8000". An https:// address on a
 * private network becomes http:// — the demo server has no TLS, and HTTPS to it fails ("Invalid HTTP request"). */
export function normaliseBaseUrl(input: string): string {
  let url = input.trim();
  if (!url) throw new Error('Enter the server address, e.g. http://192.168.1.10:8000');
  if (!/^https?:\/\//i.test(url)) url = `http://${url}`;
  const host = /^https:\/\/([^/:?#]+)/i.exec(url)?.[1];
  if (host && LAN_HOST.test(host)) url = `http://${url.slice('https://'.length)}`;
  url = url.replace(/\/+$/, '').replace(/\/api\/v1$/i, '');
  return url;
}

export class ServerError extends Error {
  constructor(readonly status: number, message: string, readonly code: string | null) {
    super(message);
  }
}

async function request<T>(baseUrl: string, method: 'GET' | 'POST', path: string, auth: Pairing | null, body?: unknown): Promise<T> {
  const text = body === undefined ? '' : JSON.stringify(body);
  const headers: Record<string, string> = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) Object.assign(headers, signedHeaders(auth.deviceId, auth.secret, method, path, Date.now(), text));
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(baseUrl + path, { method, headers, body: body === undefined ? undefined : text, signal: ctrl.signal });
    const raw = await res.text();
    let json: { error?: { message?: string; code?: string } } | null = null;
    try {
      json = raw ? JSON.parse(raw) : null;
    } catch {
      json = null;
    }
    if (!res.ok) throw new ServerError(res.status, json?.error?.message ?? `HTTP ${res.status}`, json?.error?.code ?? null);
    return json as T;
  } catch (e) {
    if (e instanceof ServerError) throw e;
    throw new Error(`Cannot reach the server at ${baseUrl} — same Wi-Fi? server running?`);
  } finally {
    clearTimeout(timer);
  }
}

export async function pairWithServer(baseUrl: string, code: string, machineId: string, clientId: string): Promise<Pairing> {
  const res = await request<{ device_id: string; device_secret: string }>(baseUrl, 'POST', `${API_PREFIX}/devices/pair`, null, {
    pairing_code: code, machine_id: machineId, device_label: `tablet ${machineId}`, client_device_id: clientId,
  });
  return { baseUrl, deviceId: res.device_id, secret: res.device_secret, machineId, cursor: 0 };
}

export function fetchBootstrap(p: Pairing): Promise<BootstrapResponse> {
  return request<BootstrapResponse>(p.baseUrl, 'GET', `${API_PREFIX}/devices/bootstrap`, p);
}

/** Push pending entries, then pull changes, every SYNC_INTERVAL_MS. Offline simply retries next round. */
export class SyncService {
  private timer: ReturnType<typeof setInterval> | null = null;
  private busy = false;

  constructor(
    private readonly pairing: Pairing,
    private readonly store: LedgerStore,
    private readonly onChanges: (changes: ServerChange[]) => number,
    private readonly onRound: () => void,
  ) {}

  start(): void {
    this.stop();
    useSync.setState({ mode: 'server', baseUrl: this.pairing.baseUrl });
    void this.syncNow();
    this.timer = setInterval(() => void this.syncNow(), SYNC_INTERVAL_MS);
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  async syncNow(): Promise<void> {
    if (this.busy) return;
    if (useSync.getState().simulatedOffline) {
      useSync.setState({ online: false, lastError: 'No signal (simulated)' });
      return;
    }
    this.busy = true;
    try {
      await this.push();
      await this.pull();
      useSync.setState({ online: true, lastSyncAt: Date.now(), lastError: null });
    } catch (e) {
      const msg = e instanceof ServerError && e.status === 401
        ? 'Server does not recognise this tablet (server reset?) — pair again in setup'
        : (e as Error).message;
      useSync.setState({ online: false, lastError: msg });
    } finally {
      this.busy = false;
      this.onRound();
    }
  }

  private async push(): Promise<void> {
    for (;;) {
      const batch: LedgerEntry[] = pendingForPush(this.store);
      if (!batch.length) return;
      for (const e of batch) (e as { sync_status: string }).sync_status = 'sent';
      let results: PushResult[];
      try {
        results = (await request<{ results: PushResult[] }>(this.pairing.baseUrl, 'POST', `${API_PREFIX}/sync/push`, this.pairing,
          pushBody(batch, this.pairing.deviceId))).results;
      } catch (e) {
        for (const entry of batch) (entry as { sync_status: string }).sync_status = 'pending';  // retry next round
        throw e;
      }
      const { rejected } = applyPushResults(batch, results);
      if (rejected.length) useSync.setState((s) => ({ rejected: [...rejected, ...s.rejected].slice(0, 20) }));
    }
  }

  private async pull(): Promise<void> {
    for (;;) {
      const res = await request<{ changes: ServerChange[]; next_cursor: number; has_more: boolean }>(
        this.pairing.baseUrl, 'GET', pullPath(this.pairing.cursor), this.pairing);
      if (res.changes.length) {
        const applied = this.onChanges(res.changes);
        useSync.setState((s) => ({ changesApplied: s.changesApplied + applied }));
      }
      this.pairing.cursor = res.next_cursor;
      savePairing(this.pairing);
      if (!res.has_more) return;
    }
  }
}
