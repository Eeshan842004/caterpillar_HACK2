// EngineHost (technical spec §4.4, T18): builds the engine from the bundled seed, runs the 1 s tick loop on a
// simulated clock (presenter speed 1×/10×/60×), and publishes snapshots to the Zustand store.
import {
  type Command, type CommandResult, type DemoSeed, type EngineSnapshot, LiveSimulator, type MachineProfile,
  MemoryLedgerStore, ShiftEngine, SimClock, deviceDataFromSeed,
} from '@shiftmate/core';
import excavator from '@shiftmate/content/profiles/excavator_20t.v1.json';
import haulTruck from '@shiftmate/content/profiles/haul_truck_90t.v1.json';
import wheelLoader from '@shiftmate/content/profiles/wheel_loader_950.v1.json';
import seedJson from '@shiftmate/content/seed/demo_seed.json';
import historyJson from '@shiftmate/content/seed/demo_history.json';
import { create } from 'zustand';
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
  snapshot: EngineSnapshot | null;
  speed: number;
  presenterOpen: boolean;
  lastMessage: string | null;
}

export const useHost = create<HostState>(() => ({
  paired: null, snapshot: null, speed: 1, presenterOpen: false, lastMessage: null,
}));

class EngineHost {
  engine: ShiftEngine | null = null;
  sim: LiveSimulator | null = null;
  private clock: SimClock | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;
  readonly deviceId = uuid();

  pair(machineId: string): void {
    const now = Date.now();
    const data = deviceDataFromSeed(seed, historyJson as unknown[], machineId, now);
    const profile = PROFILES[data.machine.profile_id];
    if (!profile) throw new Error(`No profile ${data.machine.profile_id}`);
    this.clock = new SimClock(now);
    this.engine = new ShiftEngine({ ...data, profile, artifact: null, device_id: this.deviceId, data_origin: 'live',
      clock: this.clock, newId: uuid, store: new MemoryLedgerStore() });
    const zone = data.zones.find((z) => z.zone_id === data.assignments[0]?.zone_id) ?? data.zones[0];
    this.sim = new LiveSimulator(profile, { lat: zone?.center_lat ?? data.site.lat, lon: zone?.center_lon ?? data.site.lon });
    useHost.setState({ paired: machineId, snapshot: this.engine.snapshot() });
    this.restartTimer();
  }

  unpair(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.engine = null;
    this.sim = null;
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
