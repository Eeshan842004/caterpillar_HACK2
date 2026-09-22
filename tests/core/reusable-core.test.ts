import { describe, expect, it } from 'vitest';
import {
  ConsequentialActionPolicy,
  FixedClock,
  OfflineActionQueue,
  SequenceIdGenerator,
} from '@/core';

describe('Reusable starter core', () => {
  it('creates replayable queue metadata with injected time and identifiers', () => {
    const queue = new OfflineActionQueue(
      new FixedClock('2026-09-22T00:00:00.000Z'),
      new SequenceIdGenerator('drill')
    );

    const item = queue.enqueue({ observation: 'Guard rail damaged' });

    expect(item.idempotency_key).toBe('idemp_drill_0001');
    expect(item.client_id).toBe('local_drill_0002');
    expect(item.created_at).toBe('2026-09-22T00:00:00.000Z');
    expect(item.sync_status).toBe('PENDING');

    queue.markSynced(item);
    expect(queue.wasSynced(item.idempotency_key)).toBe(true);
    expect(queue.pending()).toHaveLength(0);
  });

  it('keeps failed actions visible for a later retry', () => {
    const queue = new OfflineActionQueue<Record<string, string>>();
    const item = queue.enqueue({ observation: 'Guard rail damaged' });

    queue.markFailed(item, new Error('network unavailable'));

    expect(item.sync_status).toBe('FAILED');
    expect(item.last_error).toBe('network unavailable');
    expect(queue.pending()).toEqual([item]);
  });

  it('applies the human-confirmation boundary without fleet terminology', () => {
    const policy = new ConsequentialActionPolicy();

    expect(
      policy.validate({
        target_id: 'hazard_001',
        title: 'Close affected walkway',
        approved_by: 'Safety Lead',
        approved_at: '2026-09-22T00:00:00.000Z',
      }).isValid
    ).toBe(true);

    const rejected = policy.validate({
      target_id: 'hazard_001',
      title: 'Close affected walkway',
    });
    expect(rejected.isValid).toBe(false);
    expect(rejected.violations.some((violation) => violation.includes('ADR-0003'))).toBe(true);
  });

  it('generates the same audit hash regardless of snapshot key insertion order', () => {
    const policy = new ConsequentialActionPolicy();
    const base = {
      id: 'audit_001',
      timestamp: '2026-09-22T00:00:00.000Z',
      actor_name: 'Safety Lead',
      actor_role: 'Reviewer',
      action: 'HAZARD_ACTION_APPROVED',
      target_id: 'hazard_001',
      details: 'Approved temporary closure',
    };

    const first = policy.generateAuditHash({
      ...base,
      payload_snapshot: { severity: 'HIGH', site: 'north' },
    });
    const second = policy.generateAuditHash({
      ...base,
      payload_snapshot: { site: 'north', severity: 'HIGH' },
    });

    expect(first).toBe(second);
  });
});
