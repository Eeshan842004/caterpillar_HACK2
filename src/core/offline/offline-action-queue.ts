import {
  type Clock,
  type IdGenerator,
  randomIdGenerator,
  systemClock,
} from '../runtime/determinism';

export type SyncStatus = 'PENDING' | 'SYNCED' | 'FAILED';

export interface QueuedAction<Payload> {
  idempotency_key: string;
  client_id: string;
  payload: Payload;
  created_at: string;
  sync_status: SyncStatus;
  last_error?: string;
}

/**
 * Challenge-neutral in-memory queue.
 *
 * This is a deterministic demo baseline, not durable offline storage. A
 * cartridge that requires refresh/restart persistence must provide a durable
 * adapter while preserving this contract.
 */
export class OfflineActionQueue<Payload> {
  private items: QueuedAction<Payload>[] = [];
  private syncedKeys = new Set<string>();

  constructor(
    private readonly clock: Clock = systemClock,
    private readonly ids: IdGenerator = randomIdGenerator
  ) {}

  public enqueue(payload: Payload): QueuedAction<Payload> {
    const item: QueuedAction<Payload> = {
      idempotency_key: this.ids.next('idemp'),
      client_id: this.ids.next('local'),
      payload,
      created_at: this.clock.now().toISOString(),
      sync_status: 'PENDING',
    };
    this.items.push(item);
    return item;
  }

  public pending(): QueuedAction<Payload>[] {
    // Failed sends remain outstanding and visible so the caller can retry them.
    return this.items.filter((item) => item.sync_status !== 'SYNCED');
  }

  public all(): QueuedAction<Payload>[] {
    return this.items;
  }

  public wasSynced(idempotencyKey: string): boolean {
    return this.syncedKeys.has(idempotencyKey);
  }

  public markSynced(item: QueuedAction<Payload>): void {
    item.sync_status = 'SYNCED';
    item.last_error = undefined;
    this.syncedKeys.add(item.idempotency_key);
  }

  public markFailed(item: QueuedAction<Payload>, error: unknown): void {
    item.sync_status = 'FAILED';
    item.last_error = error instanceof Error ? error.message : String(error);
  }

  public clear(): void {
    this.items = [];
    this.syncedKeys.clear();
  }
}
