// Worked examples from the technical spec (§8.1–§8.9) as executable checks.
import { describe, expect, it } from 'vitest';
import excavatorJson from '@shiftmate/content/profiles/excavator_20t.v1.json';
import truckJson from '@shiftmate/content/profiles/haul_truck_90t.v1.json';
import {
  AlertManager, IdleTracker, Ledger, MachineStateMachine, MemoryLedgerStore, SafeExitGuard, SeatbeltRules, SignalStore,
  baselineMinutes, candidateState, impactPreview, liveUpdate, proximityLevel, sequentialIds, timeAccounting,
  type DetectionEvent, type MachineProfile, type Site, type TaskAssignment,
} from '../src';

const excavator = excavatorJson as unknown as MachineProfile;
const truck = truckJson as unknown as MachineProfile;
const site: Site = {
  site_id: 'SITE-CHN-01', name: 'Chennai', sector: 'construction', lat: 12.83, lon: 79.95, utc_offset_minutes: 330,
  diesel_price_inr_per_l: 92, dark_start_local: '19:00', dark_end_local: '06:00', job_efficiency_override: null,
  congestion_level: 'medium',
};
const T0 = Date.UTC(2026, 8, 23, 7, 0, 0); // 12:30 site-local

function feed(store: SignalStore, ts: number, values: Record<string, unknown>) {
  store.ingest({ ts, values: values as never });
}

const working = { engine_on: true, ground_speed_kmh: 0, hydraulic_lockout: false, load_factor_pct: 55, implement_active: true,
  seatbelt_fastened: true, seat_occupied: true, cab_door_open: false, implement_neutral: false };

describe('baseline §8.6.1 (TC-09)', () => {
  it('reproduces the three worked examples', () => {
    expect(baselineMinutes(excavator, site, 'trenching', 'clay', 40)).toBeCloseTo(49.7, 1);
    expect(baselineMinutes(excavator, site, 'truck_loading', 'clay', 60)).toBeCloseTo(28.5, 1);
    expect(baselineMinutes(truck, site, 'haul_overburden', 'overburden', 1600)).toBeCloseTo(256, 0);
  });
  it('uses the per-site job efficiency override (product F4)', () => {
    const slow = { ...site, job_efficiency_override: 0.5 };
    expect(baselineMinutes(excavator, slow, 'trenching', 'clay', 40)).toBeCloseTo((40 / (58 * 0.5)) * 60, 5);
  });
});

describe('machine state §8.1 (TC-01, TC-02)', () => {
  it('derives every branch and treats stale signals as UNKNOWN', () => {
    const s = new SignalStore(excavator);
    feed(s, T0, { ...working, engine_on: false });
    expect(candidateState(s, excavator, T0).candidate).toBe('OFF');
    feed(s, T0, { ...working, ground_speed_kmh: 6 });
    expect(candidateState(s, excavator, T0).candidate).toBe('TRAVELLING');
    feed(s, T0, { ...working, hydraulic_lockout: true });
    expect(candidateState(s, excavator, T0).candidate).toBe('SECURED');
    feed(s, T0, { ...working, load_factor_pct: 25, implement_active: false });
    expect(candidateState(s, excavator, T0).candidate).toBe('WORKING');
    feed(s, T0, { ...working, load_factor_pct: 5, implement_active: false });
    expect(candidateState(s, excavator, T0).candidate).toBe('READY');
    expect(candidateState(s, excavator, T0 + 5000).candidate).toBe('UNKNOWN'); // everything stale after 5 s
  });
  it('debounces: two evaluations to switch, TRAVELLING immediately', () => {
    const s = new SignalStore(excavator);
    const sm = new MachineStateMachine(excavator, T0);
    for (let t = 0; t < 3; t++) {
      feed(s, T0 + t * 1000, working);
      sm.evaluate(s, T0 + t * 1000);
    }
    expect(sm.state).toBe('WORKING');
    feed(s, T0 + 3000, { ...working, hydraulic_lockout: true, load_factor_pct: 5, implement_active: false });
    sm.evaluate(s, T0 + 3000);
    expect(sm.state).toBe('WORKING');
    feed(s, T0 + 4000, { ...working, hydraulic_lockout: true, load_factor_pct: 5, implement_active: false });
    sm.evaluate(s, T0 + 4000);
    expect(sm.state).toBe('SECURED');
    feed(s, T0 + 5000, { ...working, ground_speed_kmh: 12 });
    sm.evaluate(s, T0 + 5000);
    expect(sm.state).toBe('TRAVELLING');
  });
});

function alertHarness() {
  const ids = sequentialIds('a');
  const emitted: string[] = [];
  const alerts = new AlertManager(ids, (subtype, a) => emitted.push(`${a.alert_type}:${subtype}`), 'excavator');
  return { alerts, emitted };
}

describe('seatbelt §8.2 (TC-03)', () => {
  it('warns after 2 s while digging, clears when secured, never shows OK when the signal is gone', () => {
    const { alerts } = alertHarness();
    const belt = new SeatbeltRules(excavator, alerts);
    const s = new SignalStore(excavator);
    feed(s, T0, { ...working, seatbelt_fastened: false });
    belt.evaluate(s, 'WORKING', T0);
    expect(alerts.active()).toHaveLength(0);
    feed(s, T0 + 1000, { ...working, seatbelt_fastened: false });
    belt.evaluate(s, 'WORKING', T0 + 1000);
    expect(alerts.active()[0]?.alert_type).toBe('A-BELT-OPER');
    expect(alerts.drainSpeech()[0]?.text).toBe('Seatbelt. Machine operating.');
    feed(s, T0 + 2000, { ...working, seatbelt_fastened: false, hydraulic_lockout: true });
    belt.evaluate(s, 'SECURED', T0 + 2000);
    expect(alerts.active()).toHaveLength(0);
    feed(s, T0 + 6000, { engine_on: true, ground_speed_kmh: 0, hydraulic_lockout: false, load_factor_pct: 55 });
    belt.evaluate(s, 'WORKING', T0 + 6000);
    belt.evaluate(s, 'WORKING', T0 + 6000);
    expect(belt.pill).toBe('unavailable');
    expect(alerts.active()[0]?.alert_type).toBe('A-BELT-UNAV');
  });
  it('acknowledging stops repeats but keeps the hazard active (TC-06)', () => {
    const { alerts } = alertHarness();
    alerts.raise('A-BELT-OPER', 'WARNING', 'belt', {}, T0);
    alerts.ack(T0 + 1000);
    expect(alerts.active()[0]?.status).toBe('ACKNOWLEDGED');
    alerts.drainSpeech();
    alerts.tickRepeats(T0 + 25_000);
    expect(alerts.drainSpeech()).toHaveLength(0);
    alerts.clear('belt', 'fastened', T0 + 26_000);
    const again = alerts.raise('A-BELT-OPER', 'WARNING', 'belt', {}, T0 + 40_000);
    expect(again.occurrences).toBe(2); // reopened within 60 s: same alert id
  });
});

describe('Safe Exit Guard §8.2 (TC-72)', () => {
  function run(steps: [number, Record<string, unknown>, 'WORKING' | 'SECURED' | 'READY'][]) {
    const { alerts, emitted } = alertHarness();
    const guard = new SafeExitGuard(excavator, alerts);
    const s = new SignalStore(excavator);
    for (const [t, values, state] of steps) {
      feed(s, T0 + t * 1000, { ...working, ...values });
      guard.evaluate(s, state, T0 + t * 1000);
    }
    return { guard, emitted, alerts };
  }

  it('belt-off alone never opens the advisory', () => {
    const { guard, emitted } = run([[0, {}, 'WORKING'], [1, { seatbelt_fastened: false }, 'WORKING'], [5, { seatbelt_fastened: false }, 'WORKING']]);
    expect(guard.view.active).toBe(false);
    expect(emitted.some((e) => e.startsWith('A-EXIT-UNSEC'))).toBe(false);
  });
  it('belt-off + door open within 10 s while unsecured → advisory; securing clears it', () => {
    const { guard, emitted } = run([
      [0, {}, 'WORKING'], [1, { seatbelt_fastened: false }, 'WORKING'], [4, { seatbelt_fastened: false, cab_door_open: true }, 'READY'],
    ]);
    expect(guard.view.active).toBe(true);
    expect(guard.view.checklist.secure_signal).toBe('not_yet');
    const s = new SignalStore(excavator);
    void s;
    expect(emitted).toContain('A-EXIT-UNSEC:raised');
  });
  it('clears on seat and door restored, and on "Not exiting"', () => {
    const a = run([[0, {}, 'WORKING'], [1, { seatbelt_fastened: false }, 'WORKING'], [3, { seatbelt_fastened: false, seat_occupied: false }, 'READY'],
      [5, { seatbelt_fastened: false, seat_occupied: true, cab_door_open: false }, 'READY']]);
    expect(a.guard.view.active).toBe(false);
    const b = run([[0, {}, 'WORKING'], [1, { seatbelt_fastened: false }, 'WORKING'], [3, { seatbelt_fastened: false, cab_door_open: true }, 'READY']]);
    b.guard.cancel(T0 + 4000);
    expect(b.guard.view.active).toBe(false);
    expect(b.emitted).toContain('A-EXIT-UNSEC:acknowledged');
  });
  it('door opening 12 s after the belt transition is outside the window', () => {
    const { guard } = run([[0, {}, 'WORKING'], [1, { seatbelt_fastened: false }, 'WORKING'], [13, { seatbelt_fastened: false, cab_door_open: true }, 'READY']]);
    expect(guard.view.active).toBe(false);
  });
  it('stale guard inputs are reported unavailable, never as secured', () => {
    const { alerts } = alertHarness();
    const guard = new SafeExitGuard(excavator, alerts);
    const s = new SignalStore(excavator);
    feed(s, T0, { engine_on: true, ground_speed_kmh: 0 });
    guard.evaluate(s, 'UNKNOWN', T0);
    expect(guard.view.checklist.secure_signal).toBe('unavailable');
    expect(guard.view.unavailable_signals).toContain('implement_neutral');
  });
});

describe('proximity §8.4 worked example (TC-07)', () => {
  const person = (distance_m: number, closing_mps: number): DetectionEvent =>
    ({ ts: T0, object_id: 'P1', type: 'person', bearing_deg: 180, distance_m, closing_mps, quality: 0.9 });
  it('same distance: dry none, rain CAUTION; departing none; close person while digging CRITICAL', () => {
    expect(proximityLevel(person(10.5, 1.2), excavator, 1, true, 'none')).toBeNull();
    expect(proximityLevel(person(10.5, 1.2), excavator, 1.25, true, 'none')).toBe('CAUTION');
    expect(proximityLevel(person(7, -1.0), excavator, 1, true, 'none')).toBeNull();
    expect(proximityLevel(person(3, -1.0), excavator, 1, true, 'none')).toBe('CRITICAL');
  });
});

describe('live update §8.6.6 (TC-12)', () => {
  it('reproduces 46.0 / 41.1 / 52.3 and never goes negative', () => {
    const r = liveUpdate({ now: T0, prior: { p10: 46, p50: 53, p90: 62 }, quantity: 40, progress: 8, activeElapsedMin: 12,
      paused: false, expectedWaitMin: 0, waitingSoFarMin: 0, siteDelayInProgress: null });
    // T11: worked examples must reproduce to 0.1 min (the spec rounds intermediate values)
    expect(Math.abs(r.rem50 - 46.0)).toBeLessThanOrEqual(0.1);
    expect(Math.abs(r.rem10 - 41.1)).toBeLessThanOrEqual(0.1);
    expect(Math.abs(r.rem90 - 52.3)).toBeLessThanOrEqual(0.1);
    const late = liveUpdate({ now: T0, prior: { p10: 46, p50: 53, p90: 62 }, quantity: 40, progress: 0, activeElapsedMin: 80,
      paused: true, expectedWaitMin: 5, waitingSoFarMin: 20, siteDelayInProgress: null });
    expect(late.rem50).toBeGreaterThan(0);
    expect(late.mode).toBe('conditional');
  });
});

describe('time accounting §8.6.7 (TC-13)', () => {
  const at = (h: number, m: number) => Date.UTC(2026, 8, 23, h, m);
  it('truck wait moves time to waiting; correcting to break moves it to break', () => {
    const intervals = [{ state: 'ACTIVE' as const, start: at(13, 15), end: at(14, 20) }];
    expect(timeAccounting(intervals, [{ start: at(13, 40), end: at(13, 52), category: 'site_delay' }], at(14, 20)))
      .toEqual({ active_min: 53, waiting_min: 12, break_min: 0, paused_min: 0 });
    expect(timeAccounting(intervals, [{ start: at(13, 40), end: at(13, 52), category: 'break' }], at(14, 20)))
      .toEqual({ active_min: 53, waiting_min: 0, break_min: 12, paused_min: 0 });
  });
});

describe('downstream impact §8.6.9 (TC-73)', () => {
  const next = (start: number | null, window = 15): TaskAssignment => ({
    task_id: 'T2', site_id: 's', machine_id: 'EX-07', task_type: 'truck_loading', zone_id: null, location_text: '', quantity: 60,
    unit: 'm3', material: 'clay', priority: 2, completion_criterion: '', planner_minutes: 25, planned_date: '2026-09-23',
    planned_start_at: start, planned_start_window_min: window, sequence: 2, source: 'seed', revision: 1, status: 'assigned',
  });
  const start = T0 + 60 * 60_000;
  it('measures risk against the window end, not the nominal start', () => {
    const inside = impactPreview({ currentTaskId: 'T1', finish50Before: start - 20 * 60_000, finish50After: start + 10 * 60_000,
      finish90After: start + 12 * 60_000, next: next(start) });
    expect(inside.risk).toBe('none');
    expect(inside.current_delta_min).toBe(30);
    const hard = impactPreview({ currentTaskId: 'T1', finish50Before: start, finish50After: start + 10 * 60_000,
      finish90After: start + 12 * 60_000, next: next(start, 0) });
    expect(hard.risk).toBe('likely_miss');
    const p90Only = impactPreview({ currentTaskId: 'T1', finish50Before: start, finish50After: start + 10 * 60_000,
      finish90After: start + 20 * 60_000, next: next(start) });
    expect(p90Only.risk).toBe('at_risk');
  });
  it('is unavailable without a next task or a planned start (F4-R11)', () => {
    const base = { currentTaskId: 'T1', finish50Before: start, finish50After: start, finish90After: start };
    expect(impactPreview({ ...base, next: null }).risk).toBe('unavailable');
    expect(impactPreview({ ...base, next: next(null) }).risk).toBe('unavailable');
  });
});

describe('idle §8.7 (TC-15)', () => {
  it('prompts once at 5:00 of non-required idle and marks it unexplained when unanswered', () => {
    const tracker = new IdleTracker(excavator, sequentialIds('i'));
    const s = new SignalStore(excavator);
    const signals: string[] = [];
    for (let t = 0; t <= 400; t++) {
      feed(s, T0 + t * 1000, { engine_on: true, ground_speed_kmh: 0, hydraulic_lockout: false, load_factor_pct: 5, coolant_temp_c: 85 });
      for (const sig of tracker.tick(s, 'READY', T0 + t * 1000, 'T1')) signals.push(`${t}:${sig.type}`);
    }
    expect(signals).toEqual(['300:recorded', '300:prompt', '360:prompt_expired']);
    feed(s, T0 + 401_000, { engine_on: true, ground_speed_kmh: 0, hydraulic_lockout: false, load_factor_pct: 55, implement_active: true });
    const [end] = tracker.tick(s, 'WORKING', T0 + 401_000, 'T1');
    expect(end?.type === 'ended' && end.ended.idle_class).toBe('unexplained');
  });
  it('cool-down after heavy load is required idle with no prompt', () => {
    const tracker = new IdleTracker(excavator, sequentialIds('i'));
    const s = new SignalStore(excavator);
    for (let t = 0; t < 600; t++) {
      feed(s, T0 + t * 1000, { ...working, load_factor_pct: 75 });
      tracker.tick(s, 'WORKING', T0 + t * 1000, 'T1');
    }
    const signals: string[] = [];
    for (let t = 600; t <= 960; t++) {
      feed(s, T0 + t * 1000, { engine_on: true, ground_speed_kmh: 0, hydraulic_lockout: true, load_factor_pct: 5, coolant_temp_c: 90 });
      for (const sig of tracker.tick(s, 'SECURED', T0 + t * 1000, null)) signals.push(sig.type);
    }
    expect(signals).toContain('recorded');
    expect(signals).not.toContain('prompt');
  });
});

describe('ledger §5.3.1 (TC-19)', () => {
  it('corrections replace the effective payload; retraction hides; history keeps everything', () => {
    let t = T0;
    const ledger = new Ledger(new MemoryLedgerStore(), { device_id: 'd', machine_id: 'EX-07', data_origin: 'live',
      newId: sequentialIds('e'), now: () => ++t });
    const report = ledger.append({ kind: 'report', subtype: 'idle_reason', source: 'reported', observed_at: T0,
      payload: { idle_event_id: 'i1', reason_code: 'waiting_truck' } }, 's', 'OP-0007');
    ledger.append({ kind: 'correction', subtype: 'idle_reason', source: 'reported', observed_at: T0, supersedes: report.entry_id,
      payload: { target_kind: 'report', target_subtype: 'idle_reason', replacement: { idle_event_id: 'i1', reason_code: 'access_blocked' } } }, 's', 'OP-0007');
    expect(ledger.current().find((e) => e.entry_id === report.entry_id)?.payload.reason_code).toBe('access_blocked');
    expect(ledger.history(report.entry_id)).toHaveLength(2);
    expect(() => ledger.append({ kind: 'inference', subtype: 'estimate', source: 'inferred', observed_at: T0, payload: {} }, null, null))
      .toThrow(/rule_or_model_version/);
  });
});
