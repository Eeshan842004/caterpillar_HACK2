import { WorkOrder, AuditEvent } from '../types';
import { IWorkOrderRepository, IAuditRepository } from '../ports/repositories';
import {
  OfflineActionQueue,
  type QueuedAction,
} from '@/core/offline/offline-action-queue';
import type { Clock, IdGenerator } from '@/core/runtime/determinism';

type WorkOrderDraft = Omit<WorkOrder, 'id' | 'approved_at'>;
export type QueuedWorkOrder = QueuedAction<WorkOrderDraft>;

export class OfflineSyncService {
  private readonly queue: OfflineActionQueue<WorkOrderDraft>;

  constructor(clock?: Clock, ids?: IdGenerator) {
    this.queue = new OfflineActionQueue(clock, ids);
  }

  /**
   * Enqueues an action while in an offline or low-connectivity state.
   */
  public enqueue(payload: WorkOrderDraft): QueuedWorkOrder {
    return this.queue.enqueue(payload);
  }

  public getPendingQueue(): QueuedWorkOrder[] {
    return this.queue.pending();
  }

  public getQueueLength(): number {
    return this.getPendingQueue().length;
  }

  /**
   * Reconciles queued actions with backend repositories using idempotency protection.
   */
  public async syncAll(
    workOrderRepo: IWorkOrderRepository,
    auditRepo: IAuditRepository
  ): Promise<{ synced: number; skipped: number }> {
    let synced = 0;
    let skipped = 0;

    for (const item of this.queue.all()) {
      if (item.sync_status === 'SYNCED' || this.queue.wasSynced(item.idempotency_key)) {
        skipped++;
        continue;
      }

      try {
        const createdOrder = await workOrderRepo.create(item.payload, item.idempotency_key);
        await auditRepo.record({
          actor_name: item.payload.approved_by,
          actor_role: 'Field Supervisor (Offline Replay)',
          action: 'WORK_ORDER_DISPATCHED',
          target_id: createdOrder.id,
          details: `Reconciled offline work order ${item.client_id} -> ${createdOrder.id} [Idempotency: ${item.idempotency_key}]`,
          payload_snapshot: {
            client_id: item.client_id,
            idempotency_key: item.idempotency_key,
          },
        });

        this.queue.markSynced(item);
        synced++;
      } catch (err) {
        this.queue.markFailed(item, err);
      }
    }

    return { synced, skipped };
  }

  public clear(): void {
    this.queue.clear();
  }

  public async syncWith(
    send: (payload: WorkOrderDraft, idempotencyKey: string) => Promise<void>
  ): Promise<{ synced: number; failed: number }> {
    let synced = 0;
    let failed = 0;

    for (const item of this.queue.all()) {
      if (item.sync_status === 'SYNCED' || this.queue.wasSynced(item.idempotency_key)) {
        continue;
      }

      try {
        await send(item.payload, item.idempotency_key);
        this.queue.markSynced(item);
        synced++;
      } catch (error) {
        this.queue.markFailed(item, error);
        failed++;
      }
    }

    return { synced, failed };
  }
}
