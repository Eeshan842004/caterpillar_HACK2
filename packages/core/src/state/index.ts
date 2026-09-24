// Signal store and machine state (technical spec §8.1).
import type { MachineProfile, MachineState, SignalName, SignalSample, SignalValue } from '../types';

interface Reading {
  value: SignalValue;
  ts: number;
}

export class SignalStore {
  private readings = new Map<SignalName, Reading>();
  private lastCycleIncrease: number | null = null;

  constructor(private readonly profile: MachineProfile) {}

  ingest(sample: SignalSample): void {
    for (const [name, value] of Object.entries(sample.values) as [SignalName, SignalValue][]) {
      if (value === undefined) continue;
      if (name === 'load_cycles') {
        const prev = this.readings.get('load_cycles');
        if (prev && typeof prev.value === 'number' && typeof value === 'number' && value > prev.value) {
          this.lastCycleIncrease = sample.ts;
        }
      }
      this.readings.set(name, { value, ts: sample.ts });
    }
  }

  /** Present and younger than the profile's freshness limit. A missing signal is never "fresh". */
  fresh(name: SignalName, now: number): boolean {
    const r = this.readings.get(name);
    const limit = this.profile.signals[name]?.freshness_ms;
    return r !== undefined && limit !== undefined && now - r.ts <= limit;
  }

  value(name: SignalName): SignalValue | undefined {
    return this.readings.get(name)?.value;
  }

  bool(name: SignalName, now: number): boolean | null {
    if (!this.fresh(name, now)) return null;
    const v = this.value(name);
    return typeof v === 'boolean' ? v : null;
  }

  num(name: SignalName, now: number): number | null {
    if (!this.fresh(name, now)) return null;
    const v = this.value(name);
    return typeof v === 'number' ? v : null;
  }

  age(name: SignalName, now: number): number | null {
    const r = this.readings.get(name);
    return r ? now - r.ts : null;
  }

  get lastLoadCycleIncrease(): number | null {
    return this.lastCycleIncrease;
  }
}

export interface StateResult {
  candidate: MachineState;
  reason: string;
}

/** Candidate state per §8.1; S = profile.secure_signal. */
export function candidateState(store: SignalStore, profile: MachineProfile, now: number): StateResult {
  const t = profile.state_thresholds;
  const S = profile.secure_signal;
  if (!store.fresh('engine_on', now)) return { candidate: 'UNKNOWN', reason: 'engine_on_stale' };
  if (store.value('engine_on') === false) return { candidate: 'OFF', reason: 'engine_off' };
  const speed = store.num('ground_speed_kmh', now);
  if (speed === null) return { candidate: 'UNKNOWN', reason: 'ground_speed_stale' };
  if (speed > t.travel_speed_kmh) return { candidate: 'TRAVELLING', reason: 'speed_above_travel' };
  if (!store.fresh(S, now)) return { candidate: 'UNKNOWN', reason: `${S}_stale` };
  if (store.value(S) === true && speed < t.stationary_speed_kmh) return { candidate: 'SECURED', reason: `${S}_engaged` };
  const load = store.num('load_factor_pct', now);
  if (load === null) return { candidate: 'UNKNOWN', reason: 'load_factor_stale' };
  const implementActive = store.bool('implement_active', now) === true;
  const lastInc = store.lastLoadCycleIncrease;
  const cycling = lastInc !== null && now - lastInc <= t.load_cycle_window_s * 1000;
  const working = load >= t.working_load_factor_pct || implementActive || cycling;
  return working ? { candidate: 'WORKING', reason: 'working' } : { candidate: 'READY', reason: 'ready' };
}

/** Debounced machine state: UNKNOWN and TRAVELLING switch immediately; others need `debounce_s` evaluations. */
export class MachineStateMachine {
  private current: MachineState = 'UNKNOWN';
  private since: number;
  private pending: MachineState | null = null;
  private pendingCount = 0;

  constructor(private readonly profile: MachineProfile, now: number) {
    this.since = now;
  }

  get state(): MachineState {
    return this.current;
  }

  get stateSince(): number {
    return this.since;
  }

  /** Returns the transition when the state changes on this evaluation. */
  evaluate(store: SignalStore, now: number): { from: MachineState; to: MachineState; reason: string } | null {
    const { candidate, reason } = candidateState(store, this.profile, now);
    if (candidate === this.current) {
      this.pending = null;
      this.pendingCount = 0;
      return null;
    }
    const immediate = candidate === 'UNKNOWN' || candidate === 'TRAVELLING';
    if (this.pending === candidate) this.pendingCount += 1;
    else {
      this.pending = candidate;
      this.pendingCount = 1;
    }
    if (immediate || this.pendingCount >= this.profile.state_thresholds.debounce_s) {
      const from = this.current;
      this.current = candidate;
      this.since = now;
      this.pending = null;
      this.pendingCount = 0;
      return { from, to: candidate, reason };
    }
    return null;
  }
}
