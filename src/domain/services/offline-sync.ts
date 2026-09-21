import { WorkOrder, AuditEvent } from '../types';
import { IWorkOrderRepository, IAuditRepository } from '../ports/repositories';

export interface QueuedWorkOrder {
  idempotency_key: string;
  client_id: string;
  payload: Omit<WorkOrder, 'id' | 'approved_at'>;
  created_at: string;
  sync_status: 'PENDING' | 'SYNCED' | 'FAILED';
}

export class OfflineSyncService {
  private queue: QueuedWorkOrder[] = [];
  private syncedKeys: Set<string> = new Set();

  /**
   * Enqueues an action while in an offline or low-connectivity state.
   */
  public enqueue(payload: Omit<WorkOrder, 'id' | 'approved_at'>): QueuedWorkOrder {
    const item: QueuedWorkOrder = {
      idempotency_key: `idemp_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
      client_id: `wo_local_${Date.now()}`,
      payload,
      created_at: new Date().toISOString(),
      sync_status: 'PENDING',
    };
    this.queue.push(item);
    return item;
  }

  public getPendingQueue(): QueuedWorkOrder[] {
    return this.queue.filter((item) => item.sync_status === 'PENDING');
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

    for (const item of this.queue) {
      if (item.sync_status === 'SYNCED' || this.syncedKeys.has(item.idempotency_key)) {
        skipped++;
        continue;
      }

      try {
        const createdOrder = await workOrderRepo.create(item.payload);
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

        item.sync_status = 'SYNCED';
        this.syncedKeys.add(item.idempotency_key);
        synced++;
      } catch (err) {
        item.sync_status = 'FAILED';
      }
    }

    return { synced, skipped };
  }

  public clear(): void {
    this.queue = [];
    this.syncedKeys.clear();
  }
}
