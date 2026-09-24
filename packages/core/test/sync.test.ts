// Server sync helpers (§6.1 signing, §6.2 bootstrap/push/pull, §5.5 idempotency).
import { describe, expect, it } from 'vitest';
import excavatorJson from '@shiftmate/content/profiles/excavator_20t.v1.json';
import estimatorJson from '@shiftmate/content/models/estimator.excavator.v1.json';
import seedJson from '@shiftmate/content/seed/demo_seed.json';
import historyJson from '@shiftmate/content/seed/demo_history.json';
import {
  type BootstrapResponse, type DemoSeed, type LedgerEntry, type MachineProfile, LiveSimulator, MemoryLedgerStore, ShiftEngine,
  SimClock, applyPushResults, deviceDataFromBootstrap, deviceDataFromSeed, pendingForPush, pushBody, sequentialIds,
  signRequest, toWire,
} from '../src';

const SECRET = '00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff';
const TS = 1790000000123;
const NOW = Date.UTC(2026, 8, 23, 7, 10, 0);
const profile = excavatorJson as unknown as MachineProfile;

function engineWith(store = new MemoryLedgerStore(), artifact: unknown = null) {
  const clock = new SimClock(NOW);
  const data = deviceDataFromSeed(seedJson as unknown as DemoSeed, historyJson as unknown[], 'EX-07', NOW);
  const engine = new ShiftEngine({ ...data, profile, artifact: artifact as never, device_id: 'dev-1', data_origin: 'live',
    clock, newId: sequentialIds('x'), store });
  return { engine, clock, store, data };
}

describe('signRequest', () => {
  it('matches the server (Python hmac/hashlib) for POST and GET', () => {
    // Expected values computed with server/shiftmate/security/device_auth.py's canonical form
    expect(signRequest(SECRET, 'POST', '/api/v1/sync/push', TS, '{"batch":[]}'))
      .toBe('7c5f99e5a932a71c939c600584d4c5a9161e6d480cc3c14257e4052636a4bc16');
    expect(signRequest(SECRET, 'GET', '/api/v1/sync/pull?cursor=0&limit=200', TS, ''))
      .toBe('770abc6023f00bc469b1beb523e9a6296422691fddcd66b035eb9ce941925a06');
  });
});

describe('push', () => {
  it('sends pending shareable entries as stable wire entries and applies the verdicts', () => {
    const { engine, store } = engineWith();
    expect(engine.dispatch({ type: 'SIGN_IN', operator_id: 'OP-0007', pin: '1234' }).ok).toBe(true);
    engine.dispatch({ type: 'ACK_HANDOVER', item_id: 'all' });
    const pending = pendingForPush(store);
    expect(pending.map((e) => `${e.kind}/${e.subtype}`)).toEqual(
      ['shift_event/start', 'handover_item/acknowledged', 'handover_item/acknowledged']);

    const wire = toWire(pending[0] as LedgerEntry, 'dev-server');
    expect(wire).not.toHaveProperty('sync_status');           // retries must hash identically (§5.5)
    expect(wire.device_id).toBe('dev-server');
    expect(wire.observed_at).toBe(new Date(NOW).toISOString());
    const body = pushBody(pending, 'dev-server') as { batch: { entry_id: string; body: { kind: string } }[] };
    expect(body.batch[0]?.body.kind).toBe('ledger_entry');

    const out = applyPushResults(pending, [
      { entry_id: pending[0]!.entry_id, status: 'confirmed', reason: null },
      { entry_id: pending[1]!.entry_id, status: 'duplicate', reason: null },
      { entry_id: pending[2]!.entry_id, status: 'rejected', reason: 'validation_error' },
    ]);
    expect(out.confirmed).toBe(2);
    expect(out.rejected).toEqual(['handover_item/acknowledged: validation_error']);
    expect(pendingForPush(store)).toEqual([]);
    expect(engine.snapshot().pending_sync).toBe(0);
  });

  it('estimates carry task_type (server contract)', () => {
    const { engine, store } = engineWith();
    engine.dispatch({ type: 'SIGN_IN', operator_id: 'OP-0007', pin: '1234' });
    const task = engine.snapshot().tasks.find((t) => t.state === 'PLANNED')!;
    expect(engine.dispatch({ type: 'TASK_START', task_id: task.task.task_id }).ok).toBe(true);
    const est = store.all().find((e) => e.kind === 'inference' && e.subtype === 'estimate')!;
    expect(est.payload.task_type).toBe(task.task.task_type);
  });
});

describe('bootstrap and pulled changes', () => {
  const boot: BootstrapResponse = {
    cursor: 7,
    site: { site_id: 'SITE-CHN-01', name: 'Chennai', sector: 'construction', lat: 12.83, lon: 79.95, utc_offset_minutes: 330,
      diesel_price_inr_per_l: 92, dark_start_local: '19:00', dark_end_local: '06:00', job_efficiency_override: null,
      congestion_level: 'medium' },
    zones: [{ zone_id: 'Z1', site_id: 'SITE-CHN-01', name: 'Trench Area T1', kind: 'trench_area', center_lat: 12.831,
      center_lon: 79.951, radius_m: 60 }],
    machines: [{ machine_id: 'EX-07', short_id: 107, site_id: 'SITE-CHN-01', profile_id: 'excavator_20t', profile_version: 1,
      machine_class: 'excavator', model_name: '320', year_of_manufacture: 2021, detail_level: 'detailed' }],
    operators: [],
    assignments: [
      { task_id: 'T-1', site_id: 'SITE-CHN-01', machine_id: 'EX-07', task_type: 'trenching', zone_id: 'Z1',
        location_text: 'T1', quantity: 40, unit: 'm', material: 'clay', priority: 1, completion_criterion: '40 m',
        planner_minutes: 30, planned_date: '2026-09-23', planned_start_at: '2026-09-23T07:40:00.000Z', sequence: 1,
        source: 'seed', revision: 1, status: 'assigned' },
      { task_id: 'T-X', site_id: 'SITE-CHN-01', machine_id: 'HT-03', task_type: 'haul_ore', location_text: 'x', quantity: 1,
        unit: 't', material: 'ore', priority: 2, completion_criterion: '', planned_date: '2026-09-23', sequence: 1,
        source: 'seed' },
    ],
    handovers: [{ handover_id: 'H1', machine_id: 'EX-07', created_at: '2026-09-23T01:00:00.000Z', from_operator_id: 'OP-0011',
      items: [{ item_id: 'I1', item_type: 'defect', text: 'Oil temp high', audiences: ['next_operator'], status: 'open' }] }],
    scenarios: [],
    model_artifacts: [estimatorJson, { artifact_id: 'estimator.haul_truck@1', kind: 'estimator', machine_class: 'haul_truck' }],
    forecast: { site_id: 'SITE-CHN-01', hours: [{ valid_from: '2026-09-23T07:00:00.000Z', valid_to: '2026-09-23T08:00:00.000Z',
      weather: 'rain', visibility: 'moderate', visibility_m: 3000, temp_c: 29, heat_index_c: 33, wind_kmh: 12,
      precipitation_mm: 1.2, issued_at: '2026-09-22T12:30:00.000Z', source: 'seed' }] },
  };

  it('maps the server bootstrap onto the engine inputs with the class estimator', () => {
    const data = deviceDataFromBootstrap(boot, 'EX-07', []);
    expect(data.assignments.map((a) => a.task_id)).toEqual(['T-1']);
    expect(data.assignments[0]!.planned_start_at).toBe(Date.parse('2026-09-23T07:40:00.000Z'));
    expect(data.forecast[0]!.valid_from).toBe(Date.parse('2026-09-23T07:00:00.000Z'));
    expect(data.handoverItems[0]).toMatchObject({ item_id: 'I1', from_operator_id: 'OP-0011', status: 'open' });
    expect(data.artifact?.artifact_id).toBe('estimator.excavator@1');
  });

  it('applies reassignments, resolved handover items, new models and forecasts', () => {
    const { engine, data } = engineWith();
    const planned = engine.snapshot().tasks.find((t) => t.state === 'PLANNED')!.task;
    expect(engine.applyServerChange({ change_type: 'task_assignment.removed',
      payload: { task_id: planned.task_id, reason: 'reassigned' } })).toBe(true);
    expect(engine.snapshot().tasks.some((t) => t.task.task_id === planned.task_id)).toBe(false);
    expect(engine.applyServerChange({ change_type: 'task_assignment.upsert',
      payload: { ...boot.assignments[0], task_id: 'T-NEW', planned_date: data.assignments[0]!.planned_date } })).toBe(true);
    expect(engine.snapshot().tasks.some((t) => t.task.task_id === 'T-NEW')).toBe(true);

    const item = data.handoverItems[0]!;
    expect(engine.applyServerChange({ change_type: 'handover_item.resolved', payload: { item_id: item.item_id } })).toBe(true);
    expect(engine.snapshot().briefing.handover.some((h) => h.item_id === item.item_id)).toBe(false);

    expect(engine.applyServerChange({ change_type: 'model.published', payload: estimatorJson as never })).toBe(true);
    const next = engine.snapshot().tasks.find((t) => t.state === 'PLANNED' && t.task.task_type === 'trenching');
    expect(next?.estimate.basis).toBe('comparable_history');

    expect(engine.applyServerChange({ change_type: 'forecast.upsert', payload: boot.forecast as never })).toBe(true);
    expect(engine.applyServerChange({ change_type: 'followup.resolved', payload: {} })).toBe(false);
  });

  it('pushes a whole simulated shift without leaking private entries', () => {
    const { engine, store, clock } = engineWith();
    const sim = new LiveSimulator(profile, { lat: 12.831, lon: 79.951 });
    engine.dispatch({ type: 'SIGN_IN', operator_id: 'OP-0007', pin: '1234' });
    sim.preset('ready');
    for (let i = 0; i < 30; i++) {
      clock.advance(1000);
      const s = sim.step(clock.now());
      engine.tick(s.sample, s.detections, s.heartbeat);
    }
    const pending = pendingForPush(store);
    expect(pending.length).toBeGreaterThan(1);
    expect(pending.every((e) => e.audience !== 'operator_only' && e.kind !== 'learning_event')).toBe(true);
  });
});
