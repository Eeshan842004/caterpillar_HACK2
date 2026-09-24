// Server sync helpers (technical spec §6.1 signing, §6.2 pair/bootstrap/push/pull, §5.5 idempotency; T22 core part).
// Pure: no fetch, no clock — the app passes timestamps and does the I/O.
import { hmac } from '@noble/hashes/hmac.js';
import { sha256 } from '@noble/hashes/sha2.js';
import { bytesToHex, hexToBytes, utf8ToBytes } from '@noble/hashes/utils.js';
import type { EstimatorArtifact } from '../estimate';
import { type LedgerStore, syncsToServer } from '../ledger';
import type { DeviceData } from '../seed';
import type {
  ForecastHour, HandoverItemRef, LedgerEntry, MachineRef, OperatorRef, Site, SyncStatus, TaskAssignment, Unit, VisibilityBand,
  Weather, Zone,
} from '../types';
import { isoMs } from '../util';

export const API_PREFIX = '/api/v1';
export const PUSH_BATCH_MAX = 100;

export function sha256Hex(text: string): string {
  return bytesToHex(sha256(utf8ToBytes(text)));
}

/** §6.1 device signature: HMAC-SHA256(secret, "METHOD\npath?query\ntimestamp_ms\nsha256_hex(body)"), hex. */
export function signRequest(secretHex: string, method: string, pathWithQuery: string, timestampMs: number, body: string): string {
  const canonical = `${method.toUpperCase()}\n${pathWithQuery}\n${timestampMs}\n${sha256Hex(body)}`;
  return bytesToHex(hmac(sha256, hexToBytes(secretHex), utf8ToBytes(canonical)));
}

export function signedHeaders(deviceId: string, secretHex: string, method: string, pathWithQuery: string, timestampMs: number,
  body: string): Record<string, string> {
  return {
    'X-Device-Id': deviceId,
    'X-Timestamp': String(timestampMs),
    'X-Signature': signRequest(secretHex, method, pathWithQuery, timestampMs, body),
  };
}

// ------------------------------------------------------------------------------------------------ push

/** Wire shape of a ledger entry (§5.3.1): ISO times; `sync_status` is device-only and never sent, so a retried entry
 * hashes identically on the server (idempotency, §5.5). */
export function toWire(e: LedgerEntry, deviceId: string): Record<string, unknown> {
  const { sync_status: _local, ...rest } = e;
  void _local;
  return { ...rest, device_id: deviceId, observed_at: isoMs(e.observed_at), recorded_at: isoMs(e.recorded_at) };
}

/** Entries waiting to go to the server, oldest first, at most one batch. */
export function pendingForPush(store: LedgerStore, max = PUSH_BATCH_MAX): LedgerEntry[] {
  return store.all()
    .filter((e) => e.sync_status === 'pending' && syncsToServer(e))
    .sort((a, b) => a.recorded_at - b.recorded_at)
    .slice(0, max);
}

export function pushBody(entries: LedgerEntry[], deviceId: string): { batch: unknown[] } {
  return {
    batch: entries.map((e) => ({
      entry_id: e.entry_id, type: e.kind, created_at: isoMs(e.recorded_at),
      body: { kind: 'ledger_entry', entry: toWire(e, deviceId) },
    })),
  };
}

export interface PushResult {
  entry_id: string;
  status: 'confirmed' | 'duplicate' | 'needs_review' | 'rejected';
  reason: string | null;
}

/** Applies the server's per-entry verdicts to the device ledger (entries are updated in place). */
export function applyPushResults(entries: LedgerEntry[], results: PushResult[]): { confirmed: number; rejected: string[] } {
  const byId = new Map(entries.map((e) => [e.entry_id, e]));
  const rejected: string[] = [];
  let confirmed = 0;
  for (const r of results) {
    const e = byId.get(r.entry_id);
    if (!e) continue;
    const status: SyncStatus = r.status === 'duplicate' ? 'confirmed' : r.status;
    (e as { sync_status: SyncStatus }).sync_status = status;
    if (status === 'confirmed') confirmed += 1;
    if (status === 'rejected') rejected.push(`${e.kind}/${e.subtype}: ${r.reason ?? 'rejected'}`);
  }
  return { confirmed, rejected };
}

// ------------------------------------------------------------------------------------------------ pull

export interface ServerChange {
  seq: number;
  change_type: string;
  scope_type: string;
  scope_id: string | null;
  created_at: string;
  payload: Record<string, unknown>;
}

export function pullPath(cursor: number, limit = 200): string {
  return `${API_PREFIX}/sync/pull?cursor=${cursor}&limit=${limit}`;
}

// ------------------------------------------------------------------------------------------------ bootstrap

/* eslint-disable @typescript-eslint/no-explicit-any */
export interface BootstrapResponse {
  cursor: number;
  site: any;
  zones: any[];
  machines: any[];
  operators: any[];
  assignments: any[];
  handovers: any[];
  scenarios: any[];
  model_artifacts: any[];
  forecast: { site_id: string; hours: any[] };
}

const ms = (iso: string | null | undefined): number | null => (iso ? Date.parse(iso) : null);

export function forecastHourFromWire(h: any): ForecastHour {
  return {
    valid_from: Date.parse(h.valid_from), valid_to: Date.parse(h.valid_to), weather: h.weather as Weather,
    visibility: h.visibility as VisibilityBand, visibility_m: h.visibility_m ?? null, temp_c: h.temp_c,
    heat_index_c: h.heat_index_c ?? null, wind_kmh: h.wind_kmh, precipitation_mm: h.precipitation_mm,
    issued_at: Date.parse(h.issued_at), source: h.source === 'open_meteo' ? 'open_meteo' : 'seed',
  };
}

export function assignmentFromWire(a: any): TaskAssignment {
  return {
    task_id: a.task_id, site_id: a.site_id, machine_id: a.machine_id ?? null, task_type: a.task_type, zone_id: a.zone_id ?? null,
    location_text: a.location_text, quantity: a.quantity, unit: a.unit as Unit, material: a.material, priority: a.priority,
    completion_criterion: a.completion_criterion, planner_minutes: a.planner_minutes ?? null, planned_date: a.planned_date,
    planned_start_at: ms(a.planned_start_at), planned_start_window_min: a.planned_start_window_min ?? 15, sequence: a.sequence,
    source: a.source ?? 'seed', revision: a.revision ?? 1, status: a.status ?? 'assigned',
  } as TaskAssignment;
}

/** Server bootstrap (§6.2) → the engine's device data + the estimator for this machine class. `history` is the
 * device's own ledger history (bundled demo history, §5.4.2), which the server does not send back. */
export function deviceDataFromBootstrap(boot: BootstrapResponse, machineId: string, history: LedgerEntry[]):
  DeviceData & { artifact: EstimatorArtifact | null } {
  const m = boot.machines.find((x) => x.machine_id === machineId);
  if (!m) throw new Error(`Bootstrap has no machine ${machineId}`);
  const machine: MachineRef = {
    machine_id: m.machine_id, short_id: m.short_id, site_id: m.site_id, profile_id: m.profile_id,
    profile_version: m.profile_version, machine_class: m.machine_class, model_name: m.model_name,
    year_of_manufacture: m.year_of_manufacture, detail_level: m.detail_level,
  };
  const s = boot.site;
  const site: Site = {
    site_id: s.site_id, name: s.name, sector: s.sector, lat: s.lat, lon: s.lon, utc_offset_minutes: s.utc_offset_minutes,
    diesel_price_inr_per_l: s.diesel_price_inr_per_l, dark_start_local: s.dark_start_local, dark_end_local: s.dark_end_local,
    job_efficiency_override: s.job_efficiency_override ?? null, congestion_level: s.congestion_level,
  };
  const handoverItems: HandoverItemRef[] = [];
  for (const ho of boot.handovers) {
    for (const i of ho.items) {
      handoverItems.push({ item_id: i.item_id, item_type: i.item_type, text: i.text, audiences: i.audiences, status: i.status,
        task_id: i.task_id ?? null, incident_id: i.incident_id ?? null, from_operator_id: ho.from_operator_id ?? null,
        created_at: Date.parse(ho.created_at) });
    }
  }
  const artifact = (boot.model_artifacts.find((a) => a.kind === 'estimator' && a.machine_class === machine.machine_class)
    ?? null) as EstimatorArtifact | null;
  return {
    site,
    zones: boot.zones.map((z) => ({ ...z, speed_limit_kmh: z.speed_limit_kmh ?? null })) as Zone[],
    machine,
    operators: boot.operators as OperatorRef[],
    assignments: boot.assignments.filter((a) => a.machine_id === machineId).map(assignmentFromWire),
    forecast: boot.forecast.hours.map(forecastHourFromWire).sort((a, b) => a.valid_from - b.valid_from),
    handoverItems,
    history,
    artifact,
  };
}
