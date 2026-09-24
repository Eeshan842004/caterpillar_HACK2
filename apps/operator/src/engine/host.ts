// EngineHost (technical spec §4.4, T18): builds the engine from the site server's bootstrap (or, in local-only mode,
// the bundled seed), runs the 1 s tick loop on a simulated clock (presenter speed 1×/10×/60×), syncs with the server
// and publishes snapshots to the Zustand store.
import {
  type Command, type CommandResult, type DemoSeed, type DeviceData, type EngineSnapshot, type EstimatorArtifact, LiveSimulator,
  type MachineProfile, MemoryLedgerStore, type ServerChange, ShiftEngine, SimClock, deviceDataFromBootstrap, deviceDataFromSeed,
} from '@shiftmate/core';
import excavator from '@shiftmate/content/profiles/excavator_20t.v1.json';
import haulTruck from '@shiftmate/content/profiles/haul_truck_90t.v1.json';
import wheelLoader from '@shiftmate/content/profiles/wheel_loader_950.v1.json';
import seedJson from '@shiftmate/content/seed/demo_seed.json';
import historyJson from '@shiftmate/content/seed/demo_history.json';
import { create } from 'zustand';
import {
  type Pairing, SyncService, clientDeviceId, fetchBootstrap, loadPairing, normaliseBaseUrl, pairWithServer, savePairing, useSync,
} from '../sync/client';
import { speak } from '../voice/speaker';

const PROFILES: Record<string, MachineProfile> = {
  excavator_20t: excavator as unknown as MachineProfile,
  haul_truck_90t: haulTruck as unknown as MachineProfile,
  wheel_loader_950: wheelLoader as unknown as MachineProfile,
};
const seed = seedJson as unknown as DemoSeed;

export const PAIRABLE_MACHINES = seed.machines
  .filter((m: { machine_id: string }) => ['EX-07', 'HT-03', 'WL-02'].includes(m.machine_id))
  .map((m: { machine_id: string; model_name: string; site_id: string; profile_id: string }) => ({
    machine_id: m.machine_id,
    model_name: m.model_name,
    site_name: seed.sites.find((s: { site_id: string }) => s.site_id === m.site_id)?.name ?? m.site_id,
    profile_name: PROFILES[m.profile_id]?.display_name ?? m.profile_id,
    demo_code: (seed as unknown as { pairing_codes?: { code: string; machine_id: string }[] }).pairing_codes
      ?.find((c) => c.machine_id === m.machine_id)?.code ?? '',
  }));

function uuid(): string {
  // RFC 4122 v4 from the platform RNG (ids are injected into the pure core, §4.2)
  const c = globalThis.crypto as Crypto | undefined;
  if (c?.randomUUID) return c.randomUUID();
  const bytes = new Uint8Array(16);
  if (c?.getRandomValues) c.getRandomValues(bytes);
  else for (let i = 0; i < 16; i++) bytes[i] = Math.floor(Math.random() * 256);
  bytes[6] = ((bytes[6] ?? 0) & 0x0f) | 0x40;
  bytes[8] = ((bytes[8] ?? 0) & 0x3f) | 0x80;
  const h = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('');
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

export interface HostState {
  paired: string | null;
  connecting: string | null;    // e.g. "Pairing EX-07 with the server…"
  connectError: string | null;
  snapshot: EngineSnapshot | null;
  speed: number;
  presenterOpen: boolean;
  lastMessage: string | null;
}

export const useHost = create<HostState>(() => ({
  paired: null, connecting: null, connectError: null, snapshot: null, speed: 1, presenterOpen: false, lastMessage: null,
}));

class EngineHost {
  engine: ShiftEngine | null = null;
  sim: LiveSimulator | null = null;
  private clock: SimClock | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;
  private sync: SyncService | null = null;
  private store: MemoryLedgerStore | null = null;
  readonly deviceId = uuid();

  /** Local-only mode: roster, tasks and forecast from the bundled seed; nothing is sent anywhere. */
  pair(machineId: string): void {
    const data = deviceDataFromSeed(seed, historyJson as unknown[], machineId, Date.now());
    this.start(data, null, this.deviceId);
    useSync.setState({ mode: 'local', baseUrl: null, online: null, lastError: null });
  }

  /** Server mode (A0): pair with the site server, bootstrap from it, then push/pull every few seconds. */
  async connectServer(urlInput: string, code: string, machineId: string): Promise<boolean> {
    useHost.setState({ connecting: `Pairing ${machineId} with the server…`, connectError: null });
    try {
      const pairing = await pairWithServer(normaliseBaseUrl(urlInput), code.trim(), machineId, clientDeviceId(uuid));
      await this.startFromServer(pairing);
      return true;
    } catch (e) {
      useHost.setState({ connectError: (e as Error).message });
      return false;
    } finally {
      useHost.setState({ connecting: null });
    }
  }

  /** After an app reload: reconnect with the saved pairing (web keeps it; native keeps it for the session). */
  async resume(): Promise<boolean> {
    const saved = loadPairing();
    if (!saved || this.engine) return false;
    useHost.setState({ connecting: `Reconnecting ${saved.machineId} to ${saved.baseUrl}…`, connectError: null });
    try {
      await this.startFromServer(saved);
      return true;
    } catch (e) {
      useHost.setState({ connectError: `${(e as Error).message} Pair again below.` });
      savePairing(null);
      return false;
    } finally {
      useHost.setState({ connecting: null });
    }
  }

  private async startFromServer(pairing: Pairing): Promise<void> {
    const boot = await fetchBootstrap(pairing);
    // The server does not send the device's own history back: use the bundled demo history for this machine
    const history = deviceDataFromSeed(seed, historyJson as unknown[], pairing.machineId, Date.now()).history;
    const { artifact, ...data } = deviceDataFromBootstrap(boot, pairing.machineId, history);
    pairing.cursor = boot.cursor;
    savePairing(pairing);
    this.start(data, artifact, pairing.deviceId);
    if (!this.store) return;
    this.sync = new SyncService(pairing, this.store, (changes) => this.applyChanges(changes), () => this.flush());
    this.sync.start();
  }

  private start(data: DeviceData, artifact: EstimatorArtifact | null, deviceId: string): void {
    const profile = PROFILES[data.machine.profile_id];
    if (!profile) throw new Error(`No profile ${data.machine.profile_id}`);
    this.clock = new SimClock(Date.now());
    this.store = new MemoryLedgerStore();
    this.engine = new ShiftEngine({ ...data, profile, artifact, device_id: deviceId, data_origin: 'live',
      clock: this.clock, newId: uuid, store: this.store });
    const zone = data.zones.find((z) => z.zone_id === data.assignments[0]?.zone_id) ?? data.zones[0];
    this.sim = new LiveSimulator(profile, { lat: zone?.center_lat ?? data.site.lat, lon: zone?.center_lon ?? data.site.lon });
    useHost.setState({ paired: data.machine.machine_id, snapshot: this.engine.snapshot() });
    this.restartTimer();
  }

  private applyChanges(changes: ServerChange[]): number {
    if (!this.engine) return 0;
    let applied = 0;
    for (const c of changes) if (this.engine.applyServerChange(c)) applied += 1;
    return applied;
  }

  /** Presenter "Simulate no signal": the app keeps working; records wait and sync once restored. */
  setSimulatedOffline(off: boolean): void {
    useSync.setState({ simulatedOffline: off });
    if (!off) void this.sync?.syncNow();
  }

  syncNow(): void {
    void this.sync?.syncNow();
  }

  unpair(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.sync?.stop();
    this.sync = null;
    savePairing(null);
    this.engine = null;
    this.sim = null;
    this.store = null;
    useHost.setState({ paired: null, snapshot: null });
  }

  setSpeed(speed: number): void {
    useHost.setState({ speed });
    this.restartTimer();
  }

  private restartTimer(): void {
    if (this.timer) clearInterval(this.timer);
    const speed = useHost.getState().speed;
    this.timer = setInterval(() => this.step(), Math.max(16, 1000 / speed));
  }

  /** One simulated second: simulator → engine.tick → speech → snapshot. */
  step(): void {
    if (!this.engine || !this.sim || !this.clock) return;
    this.clock.advance(1000);
    const { sample, detections, heartbeat } = this.sim.step(this.clock.now());
    this.engine.tick(sample, detections, heartbeat);
    this.flush();
  }

  /** Fast-forward N simulated seconds (presenter "Fast-forward 6 min"). */
  fastForward(seconds: number): void {
    for (let i = 0; i < seconds; i++) {
      if (!this.engine || !this.sim || !this.clock) return;
      this.clock.advance(1000);
      const { sample, detections, heartbeat } = this.sim.step(this.clock.now());
      this.engine.tick(sample, detections, heartbeat);
    }
    this.flush();
  }

  dispatch(cmd: Command): CommandResult {
    if (!this.engine) return { ok: false, message: 'Not paired' };
    const result = this.engine.dispatch(cmd);
    useHost.setState({ lastMessage: result.ok ? null : result.message ?? 'Not possible now' });
    if (!result.ok && result.message) speak(result.message, 4);
    this.flush();
    return result;
  }

  flush(): void {
    if (!this.engine) return;
    for (const s of this.engine.drainSpeech()) speak(s.text, s.priority);
    useHost.setState({ snapshot: this.engine.snapshot() });
  }
}

export const host = new EngineHost();
