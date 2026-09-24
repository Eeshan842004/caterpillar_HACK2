// Live simulator driven by presenter toggles (technical spec §8.20, D-06). One sample per simulated second.
import type { DetectionEvent, MachineProfile, ObjectType, ProximityHeartbeat, SignalName, SignalSample, SignalValue } from '../types';

export type SimPreset = 'off' | 'secured' | 'ready' | 'dig' | 'travel_slow' | 'travel_fast';

export interface SimTrack {
  object_id: string;
  type: ObjectType;
  bearing_deg: number;
  distance_m: number;
  closing_mps: number;
  quality: number;
  remaining_s: number;
}

export interface SimState {
  values: Partial<Record<SignalName, SignalValue>>;
  dropped: SignalName[];
  heartbeat_on: boolean;
  tracks: SimTrack[];
}

export class LiveSimulator {
  state: SimState;
  private trackSeq = 0;

  constructor(private readonly profile: MachineProfile, start: { lat: number; lon: number }) {
    const S = profile.secure_signal;
    this.state = {
      values: {
        engine_on: false, ground_speed_kmh: 0, [S]: true, seatbelt_fastened: true, seat_occupied: true,
        cab_door_open: false, implement_neutral: true, load_factor_pct: 0, implement_active: false, swing_active: false,
        travel_direction: 'none', load_cycles: 0, progress_units: 0, coolant_temp_c: 82, regen_active: false,
        lat: start.lat, lon: start.lon, heading_deg: 90,
      },
      dropped: [],
      heartbeat_on: true,
      tracks: [],
    };
  }

  set(values: Partial<Record<SignalName, SignalValue>>): void {
    Object.assign(this.state.values, values);
  }

  preset(p: SimPreset): void {
    const S = this.profile.secure_signal;
    const base = { travel_direction: 'none', swing_active: false } as const;
    switch (p) {
      case 'off':
        this.set({ ...base, engine_on: false, ground_speed_kmh: 0, [S]: true, load_factor_pct: 0, implement_active: false, implement_neutral: true });
        break;
      case 'secured':
        this.set({ ...base, engine_on: true, ground_speed_kmh: 0, [S]: true, load_factor_pct: 8, implement_active: false, implement_neutral: true });
        break;
      case 'ready':
        this.set({ ...base, engine_on: true, ground_speed_kmh: 0, [S]: false, load_factor_pct: 8, implement_active: false, implement_neutral: true });
        break;
      case 'dig':
        this.set({ ...base, engine_on: true, ground_speed_kmh: 0, [S]: false, load_factor_pct: 55, implement_active: true, implement_neutral: false, swing_active: true });
        break;
      case 'travel_slow':
        this.set({ engine_on: true, ground_speed_kmh: 12, [S]: false, load_factor_pct: 40, implement_active: false, implement_neutral: true, travel_direction: 'forward', swing_active: false });
        break;
      case 'travel_fast':
        this.set({ engine_on: true, ground_speed_kmh: 42, [S]: false, load_factor_pct: 45, implement_active: false, implement_neutral: true, travel_direction: 'forward', swing_active: false });
        break;
    }
  }

  toggle(name: SignalName): void {
    this.state.values[name] = !this.state.values[name];
  }

  drop(name: SignalName, dropped: boolean): void {
    const set = new Set(this.state.dropped);
    if (dropped) set.add(name);
    else set.delete(name);
    this.state.dropped = [...set];
  }

  setHeartbeat(on: boolean): void {
    this.state.heartbeat_on = on;
  }

  /** Adds an object that approaches (positive closing speed) or departs (negative) for `seconds`. */
  addTrack(t: Omit<SimTrack, 'object_id' | 'remaining_s'> & { seconds: number }): string {
    const id = `${t.type === 'person' ? 'P' : 'V'}${++this.trackSeq}`;
    this.state.tracks.push({ object_id: id, type: t.type, bearing_deg: t.bearing_deg, distance_m: t.distance_m,
      closing_mps: t.closing_mps, quality: t.quality, remaining_s: t.seconds });
    return id;
  }

  addProgress(units: number): void {
    const v = this.state.values;
    v.progress_units = Number(v.progress_units ?? 0) + units;
    v.load_cycles = Number(v.load_cycles ?? 0) + 1;
  }

  step(ts: number): { sample: SignalSample; detections: DetectionEvent[]; heartbeat: ProximityHeartbeat | null } {
    const values: Partial<Record<SignalName, SignalValue>> = {};
    for (const [k, v] of Object.entries(this.state.values) as [SignalName, SignalValue][]) {
      if (!this.state.dropped.includes(k)) values[k] = v;
    }
    const detections: DetectionEvent[] = [];
    for (const t of this.state.tracks) {
      t.distance_m = Math.max(0.5, t.distance_m - t.closing_mps);
      t.remaining_s -= 1;
      detections.push({ ts, object_id: t.object_id, type: t.type, bearing_deg: t.bearing_deg,
        distance_m: t.distance_m, closing_mps: t.closing_mps, quality: t.quality });
    }
    this.state.tracks = this.state.tracks.filter((t) => t.remaining_s > 0);
    return {
      sample: { ts, values },
      detections: this.state.heartbeat_on ? detections : [],
      heartbeat: this.state.heartbeat_on ? { ts, quality: 0.9 } : null,
    };
  }
}
