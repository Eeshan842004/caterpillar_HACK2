// ShiftEngine walk-through of journey J1 with the real demo seed (Ravi on EX-07).
import { describe, expect, it } from 'vitest';
import excavatorJson from '@shiftmate/content/profiles/excavator_20t.v1.json';
import seedJson from '@shiftmate/content/seed/demo_seed.json';
import historyJson from '@shiftmate/content/seed/demo_history.json';
import { LiveSimulator, MemoryLedgerStore, ShiftEngine, SimClock, deviceDataFromSeed, sequentialIds, type DemoSeed, type MachineProfile } from '../src';

const profile = excavatorJson as unknown as MachineProfile;
// 12:40 site-local (07:10 UTC): task 1 planned 13:10, task 2 planned 14:10, rain forecast later
const NOW = Date.UTC(2026, 8, 23, 7, 10, 0);

function setup() {
  const clock = new SimClock(NOW);
  const data = deviceDataFromSeed(seedJson as unknown as DemoSeed, historyJson as unknown[], 'EX-07', NOW);
  const store = new MemoryLedgerStore();
  const engine = new ShiftEngine({ ...data, profile, artifact: null, device_id: 'dev-1', data_origin: 'live', clock,
    newId: sequentialIds('x'), store });
  const sim = new LiveSimulator(profile, { lat: 12.831, lon: 79.951 });
  const tick = (seconds: number) => {
    for (let i = 0; i < seconds; i++) {
      clock.advance(1000);
      const { sample, detections, heartbeat } = sim.step(clock.now());
      engine.tick(sample, detections, heartbeat);
    }
  };
  return { engine, sim, clock, tick, store, data };
}

describe('ShiftEngine J1', () => {
  it('maps the seed: site-local planned starts, blocked task 3, open handover', () => {
    const { data, engine } = setup();
    const t2 = data.assignments.find((t) => t.sequence === 2);
    expect(new Date(t2?.planned_start_at ?? 0).toISOString()).toBe('2026-09-23T08:40:00.000Z'); // 14:10 +05:30
    const snap = engine.snapshot();
    expect(snap.tasks.find((t) => t.task.sequence === 3)?.state).toBe('BLOCKED');
    expect(snap.briefing.handover.map((h) => h.item_type).sort()).toEqual(['blocked_task', 'defect']);
    expect(snap.briefing.risk_notes[0]).toMatch(/^Last shift: Hydraulic oil temperature high/);
  });

  it('signs in with the real PBKDF2 PIN and locks after 5 failures', () => {
    const { engine } = setup();
    for (let i = 0; i < 4; i++) expect(engine.dispatch({ type: 'SIGN_IN', operator_id: 'OP-0007', pin: '0000' }).message).toBe('PIN not recognised');
    expect(engine.dispatch({ type: 'SIGN_IN', operator_id: 'OP-0007', pin: '0000' }).message).toBe('Locked for 60 s');
    expect(engine.dispatch({ type: 'SIGN_IN', operator_id: 'OP-0007', pin: '1234' }).ok).toBe(false);
  });

  it('runs sign-in → start → belt alert → idle prompt → truck wait → downstream impact', () => {
    const { engine, sim, tick, store } = setup();
    expect(engine.dispatch({ type: 'SIGN_IN', operator_id: 'OP-0007', pin: '1234' }).ok).toBe(true);
    const snap0 = engine.snapshot();
    expect(snap0.shift?.guidance).toBe('guided');
    const trench = snap0.tasks.find((t) => t.task.sequence === 1);
    expect(trench?.estimate.basis).toBe('fallback');                       // no trained artifact yet (T36)
    expect(trench?.estimate.p50_min).toBeCloseTo(49.7, 1);
    expect(trench?.unfamiliar).toBe(true);

    engine.dispatch({ type: 'ACK_HANDOVER', item_id: 'all' });
    expect(engine.snapshot().briefing.all_acknowledged).toBe(true);

    sim.preset('dig');
    tick(3);
    expect(engine.snapshot().machine.state).toBe('WORKING');
    expect(engine.dispatch({ type: 'TASK_START', task_id: trench!.task.task_id }).ok).toBe(true);
    sim.addProgress(8);
    tick(60);

    sim.set({ seatbelt_fastened: false });
    tick(2);
    expect(engine.snapshot().alerts.top?.alert_type).toBe('A-BELT-OPER');
    expect(engine.snapshot().safe_exit.active).toBe(false);                // belt-off alone: no advisory
    sim.set({ seatbelt_fastened: true });
    tick(2);

    sim.preset('ready');
    tick(305);             // READY after the 2 s debounce, then 300 s of idle
    const prompted = engine.snapshot();
    expect(prompted.machine.state).toBe('READY');
    expect(prompted.prompt?.type).toBe('idle_reason');
    expect(prompted.prompt?.title).toBe('Why the wait?');

    expect(engine.dispatch({ type: 'PROMPT_ANSWER', prompt_id: prompted.prompt!.prompt_id, option: 'waiting_truck' }).ok).toBe(true);
    const after = engine.snapshot();
    expect(after.prompt).toBeNull();
    expect(after.impact?.current_task_id).toBe(trench!.task.task_id);
    expect(after.impact?.next_task_id).toBe('T-20260923-EX07-2');
    expect(after.impact?.current_delta_min).toBeGreaterThan(0);
    expect(['none', 'at_risk', 'likely_miss']).toContain(after.impact?.risk);

    expect(engine.dispatch({ type: 'TASK_NOTIFY_SUPERVISOR', task_id: trench!.task.task_id }).ok).toBe(true);
    expect(engine.dispatch({ type: 'TASK_NOTIFY_SUPERVISOR', task_id: trench!.task.task_id }).message).toBe('Already sent');
    const order = engine.snapshot().tasks.map((t) => t.task.task_id);
    expect(order).toEqual(['T-20260923-EX07-1', 'T-20260923-EX07-2', 'T-20260923-EX07-3']);   // never reordered

    const kinds = store.all().map((e) => `${e.kind}/${e.subtype}`);
    for (const k of ['shift_event/start', 'handover_item/acknowledged', 'inference/estimate', 'task_event/start', 'alert/raised',
      'idle_event/started', 'report/idle_reason', 'report/supervisor_notification']) expect(kinds).toContain(k);
    expect(store.all().every((e) => (e.kind !== 'alert' && e.kind !== 'inference') || e.rule_or_model_version)).toBe(true);
  });

  it('defers non-critical prompts while operating and counts them', () => {
    const { engine, sim, tick } = setup();
    engine.dispatch({ type: 'SIGN_IN_FOB', operator_id: 'OP-0011' });
    sim.preset('dig');
    tick(3);
    const task = engine.snapshot().tasks[0]!;
    engine.dispatch({ type: 'TASK_START', task_id: task.task.task_id });
    engine.dispatch({ type: 'OPEN_PROMPT', prompt: 'reassign_reason', task_id: task.task.task_id });
    const snap = engine.snapshot();
    expect(snap.prompt).toBeNull();
    expect(snap.prompts_waiting).toBe(1);
    expect(snap.alerts.budget.at(-1)?.noncritical_prompts_deferred).toBe(1);
    sim.preset('secured');
    tick(3);
    expect(engine.snapshot().prompt?.type).toBe('reassign_reason');
  });

  it('rain makes a person warning start earlier; a dropped feed is unavailable within 2 s', () => {
    const { engine, sim, tick } = setup();
    engine.dispatch({ type: 'SIGN_IN_FOB', operator_id: 'OP-0011' });
    sim.preset('dig');
    tick(3);
    sim.addTrack({ type: 'person', bearing_deg: 200, distance_m: 11.2, closing_mps: 0.2, quality: 0.9, seconds: 3 });
    tick(2);
    expect(engine.snapshot().proximity.status).toBe('clear');                // dry: 10.8 m is outside 9 m
    engine.dispatch({ type: 'CONDITION_REPORT', condition: 'rain', active: true });
    sim.addTrack({ type: 'person', bearing_deg: 200, distance_m: 11.2, closing_mps: 0.2, quality: 0.9, seconds: 3 });
    tick(2);
    const p = engine.snapshot().proximity;
    expect(p.status === 'alert' && p.level).toBe('CAUTION');                 // rain ×1.25 → outer 11.25 m
    sim.setHeartbeat(false);
    tick(3);
    expect(engine.snapshot().proximity.status).toBe('unavailable');
    expect(engine.snapshot().alerts.active.some((a) => a.alert_type === 'A-PROX-UNAV')).toBe(true);
  });
});
