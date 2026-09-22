import type {
  AssetMaintenanceClient,
  AssetDetail,
  CreateWorkOrderInput,
} from '@/cartridges/asset-maintenance/client/api-client';
import {
  InMemoryStorageContainer,
} from '@/cartridges/asset-maintenance/adapters/in-memory-storage';
import { RecommendationEngine } from '@/cartridges/asset-maintenance/domain/services/recommendation-engine';
import type {
  Asset,
  AuditEvent,
  WorkOrder,
} from '@/cartridges/asset-maintenance/domain/types';

export class ReferenceTestClient implements AssetMaintenanceClient {
  private readonly storage = new InMemoryStorageContainer();
  private readonly engine = new RecommendationEngine();

  public listAssets(): Promise<Asset[]> {
    return this.storage.assets.findAll();
  }

  public async getAsset(assetId: string): Promise<AssetDetail> {
    const asset = await this.storage.assets.findById(assetId);
    if (!asset) throw new Error(`Asset not found: ${assetId}`);

    const activeFaults = await this.storage.faults.findActiveByAsset(assetId);
    const telemetry = await this.storage.telemetry.findByAsset(assetId);
    const latest = await this.storage.telemetry.getLatestByAsset(assetId);

    return {
      asset,
      active_faults: activeFaults,
      telemetry_history: telemetry,
      latest_telemetry: latest,
      recommendation: this.engine.evaluate(asset, activeFaults, latest),
    };
  }

  public listWorkOrders(): Promise<WorkOrder[]> {
    return this.storage.workOrders.findAll();
  }

  public listAuditEvents(): Promise<AuditEvent[]> {
    return this.storage.audit.findAll();
  }

  public async createWorkOrder(input: CreateWorkOrderInput): Promise<WorkOrder> {
    if (input.idempotency_key) {
      const existing = await this.storage.workOrders.findByIdempotencyKey(
        input.idempotency_key
      );
      if (existing) return existing;
    }

    const created = await this.storage.workOrders.create(
      {
        asset_id: input.asset_id,
        recommendation_id: input.recommendation_id,
        title: input.title,
        description: input.description,
        priority: input.priority,
        status: 'DISPATCHED',
        assigned_technician: input.assigned_technician,
        approved_by: input.approved_by,
        notes: input.notes,
      },
      input.idempotency_key
    );

    await this.storage.audit.record({
      actor_name: input.approved_by,
      actor_role: 'Authorized Supervisor',
      action: 'WORK_ORDER_DISPATCHED',
      target_id: created.id,
      details: `Work order dispatched: ${created.title}`,
      payload_snapshot: { asset_id: created.asset_id },
    });

    return created;
  }

  public async reset(): Promise<void> {
    this.storage.reset();
  }
}
