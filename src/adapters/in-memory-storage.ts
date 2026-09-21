import {
  Asset,
  TelemetryPoint,
  DiagnosticFault,
  WorkOrder,
  AuditEvent,
  OperatingStatus,
  WorkOrderStatus,
} from '../domain/types';
import {
  IAssetRepository,
  ITelemetryRepository,
  IFaultRepository,
  IWorkOrderRepository,
  IAuditRepository,
} from '../domain/ports/repositories';
import {
  loadSeedAssets,
  loadSeedFaults,
  loadSeedTelemetry,
} from '../domain/fixtures/loader';

export class InMemoryAssetRepository implements IAssetRepository {
  constructor(private getAssets: () => Asset[]) {}

  public async findAll(): Promise<Asset[]> {
    return JSON.parse(JSON.stringify(this.getAssets()));
  }

  public async findById(id: string): Promise<Asset | null> {
    const asset = this.getAssets().find((a) => a.id === id);
    return asset ? JSON.parse(JSON.stringify(asset)) : null;
  }

  public async updateStatus(id: string, status: OperatingStatus): Promise<Asset | null> {
    const asset = this.getAssets().find((a) => a.id === id);
    if (!asset) return null;
    asset.status = status;
    return JSON.parse(JSON.stringify(asset));
  }
}

export class InMemoryTelemetryRepository implements ITelemetryRepository {
  constructor(private getTelemetry: () => TelemetryPoint[], private addPoint: (p: TelemetryPoint) => void) {}

  public async ingest(point: TelemetryPoint): Promise<TelemetryPoint> {
    this.addPoint(JSON.parse(JSON.stringify(point)));
    return point;
  }

  public async findByAsset(assetId: string): Promise<TelemetryPoint[]> {
    return JSON.parse(JSON.stringify(this.getTelemetry().filter((t) => t.asset_id === assetId)));
  }

  public async findByAssetAndParameter(
    assetId: string,
    parameter: string
  ): Promise<TelemetryPoint[]> {
    return JSON.parse(
      JSON.stringify(
        this.getTelemetry().filter((t) => t.asset_id === assetId && t.parameter === parameter)
      )
    );
  }

  public async getLatestByAsset(assetId: string): Promise<Record<string, TelemetryPoint>> {
    const points = this.getTelemetry().filter((t) => t.asset_id === assetId);
    const latest: Record<string, TelemetryPoint> = {};

    for (const point of points) {
      if (!latest[point.parameter] || new Date(point.observed_at) > new Date(latest[point.parameter].observed_at)) {
        latest[point.parameter] = JSON.parse(JSON.stringify(point));
      }
    }
    return latest;
  }
}

export class InMemoryFaultRepository implements IFaultRepository {
  constructor(private getFaults: () => DiagnosticFault[]) {}

  public async findAll(): Promise<DiagnosticFault[]> {
    return JSON.parse(JSON.stringify(this.getFaults()));
  }

  public async findByAsset(assetId: string): Promise<DiagnosticFault[]> {
    return JSON.parse(JSON.stringify(this.getFaults().filter((f) => f.asset_id === assetId)));
  }

  public async findActiveByAsset(assetId: string): Promise<DiagnosticFault[]> {
    return JSON.parse(
      JSON.stringify(this.getFaults().filter((f) => f.asset_id === assetId && f.is_active))
    );
  }

  public async acknowledge(id: string): Promise<DiagnosticFault | null> {
    const fault = this.getFaults().find((f) => f.id === id);
    if (!fault) return null;
    fault.is_active = false;
    return JSON.parse(JSON.stringify(fault));
  }
}

export class InMemoryWorkOrderRepository implements IWorkOrderRepository {
  constructor(private getOrders: () => WorkOrder[], private addOrder: (w: WorkOrder) => void) {}

  public async findAll(): Promise<WorkOrder[]> {
    return JSON.parse(JSON.stringify(this.getOrders()));
  }

  public async findById(id: string): Promise<WorkOrder | null> {
    const wo = this.getOrders().find((w) => w.id === id);
    return wo ? JSON.parse(JSON.stringify(wo)) : null;
  }

  public async findByAsset(assetId: string): Promise<WorkOrder[]> {
    return JSON.parse(JSON.stringify(this.getOrders().filter((w) => w.asset_id === assetId)));
  }

  public async create(order: Omit<WorkOrder, 'id' | 'approved_at'>): Promise<WorkOrder> {
    const newOrder: WorkOrder = {
      ...order,
      id: `wo_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      approved_at: new Date().toISOString(),
    };
    this.addOrder(newOrder);
    return JSON.parse(JSON.stringify(newOrder));
  }

  public async updateStatus(id: string, status: WorkOrderStatus): Promise<WorkOrder | null> {
    const wo = this.getOrders().find((w) => w.id === id);
    if (!wo) return null;
    wo.status = status;
    if (status === 'COMPLETED') {
      wo.completed_at = new Date().toISOString();
    }
    return JSON.parse(JSON.stringify(wo));
  }
}

export class InMemoryAuditRepository implements IAuditRepository {
  constructor(private getAudits: () => AuditEvent[], private addAudit: (a: AuditEvent) => void) {}

  public async record(event: Omit<AuditEvent, 'id' | 'timestamp'>): Promise<AuditEvent> {
    const newEvent: AuditEvent = {
      ...event,
      id: `aud_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      timestamp: new Date().toISOString(),
    };
    this.addAudit(newEvent);
    return JSON.parse(JSON.stringify(newEvent));
  }

  public async findAll(): Promise<AuditEvent[]> {
    return JSON.parse(JSON.stringify(this.getAudits()));
  }

  public async findByTarget(targetId: string): Promise<AuditEvent[]> {
    return JSON.parse(JSON.stringify(this.getAudits().filter((a) => a.target_id === targetId)));
  }
}

/**
 * Storage Container managing in-memory repositories with coordinated reset capability.
 */
export class InMemoryStorageContainer {
  private assetsData: Asset[] = [];
  private telemetryData: TelemetryPoint[] = [];
  private faultsData: DiagnosticFault[] = [];
  private workOrdersData: WorkOrder[] = [];
  private auditEventsData: AuditEvent[] = [];

  public readonly assets: IAssetRepository;
  public readonly telemetry: ITelemetryRepository;
  public readonly faults: IFaultRepository;
  public readonly workOrders: IWorkOrderRepository;
  public readonly audit: IAuditRepository;

  constructor() {
    this.assets = new InMemoryAssetRepository(() => this.assetsData);
    this.telemetry = new InMemoryTelemetryRepository(
      () => this.telemetryData,
      (p) => this.telemetryData.push(p)
    );
    this.faults = new InMemoryFaultRepository(() => this.faultsData);
    this.workOrders = new InMemoryWorkOrderRepository(
      () => this.workOrdersData,
      (w) => this.workOrdersData.push(w)
    );
    this.audit = new InMemoryAuditRepository(
      () => this.auditEventsData,
      (a) => this.auditEventsData.push(a)
    );

    this.reset();
  }

  public reset(): void {
    this.assetsData = loadSeedAssets();
    this.faultsData = loadSeedFaults();
    this.telemetryData = loadSeedTelemetry();
    this.workOrdersData = [];
    this.auditEventsData = [
      {
        id: `aud_init_${Date.now()}`,
        timestamp: new Date().toISOString(),
        actor_name: 'System',
        actor_role: 'Deterministic Seed Loader',
        action: 'SYSTEM_RESET',
        target_id: 'all',
        details: 'In-memory storage reset to pristine ground-truth fixtures',
        payload_snapshot: { version: 'seed_cat_2026_v1' },
      },
    ];
  }
}

export const globalStorage = new InMemoryStorageContainer();
