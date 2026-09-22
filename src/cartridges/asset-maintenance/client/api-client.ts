import type {
  Asset,
  AuditEvent,
  DiagnosticFault,
  Recommendation,
  TelemetryPoint,
  WorkOrder,
} from '../domain/types';

export interface AssetDetail {
  asset: Asset;
  active_faults: DiagnosticFault[];
  telemetry_history: TelemetryPoint[];
  latest_telemetry: Record<string, TelemetryPoint>;
  recommendation: Recommendation;
}

export interface CreateWorkOrderInput {
  asset_id: string;
  recommendation_id: string;
  title: string;
  description: string;
  priority: WorkOrder['priority'];
  assigned_technician: string;
  approved_by: string;
  notes?: string;
  idempotency_key?: string;
}

export interface AssetMaintenanceClient {
  listAssets(): Promise<Asset[]>;
  getAsset(assetId: string): Promise<AssetDetail>;
  listWorkOrders(): Promise<WorkOrder[]>;
  listAuditEvents(): Promise<AuditEvent[]>;
  createWorkOrder(input: CreateWorkOrderInput): Promise<WorkOrder>;
  reset(): Promise<void>;
}

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  error?: string;
  violations?: string[];
}

export class AssetMaintenanceApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly violations: string[] = []
  ) {
    super(message);
  }
}

/**
 * Browser client for the cartridge's single server-side state path.
 */
export class HttpAssetMaintenanceClient implements AssetMaintenanceClient {
  constructor(private readonly baseUrl = '') {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      cache: 'no-store',
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...init?.headers,
      },
    });
    const payload = (await response.json()) as ApiEnvelope<T>;

    if (!response.ok || !payload.success) {
      throw new AssetMaintenanceApiError(
        payload.error || `Request failed: ${path}`,
        response.status,
        payload.violations
      );
    }

    return payload.data;
  }

  public listAssets(): Promise<Asset[]> {
    return this.request<Asset[]>('/api/fleet');
  }

  public getAsset(assetId: string): Promise<AssetDetail> {
    return this.request<AssetDetail>(`/api/assets/${encodeURIComponent(assetId)}`);
  }

  public listWorkOrders(): Promise<WorkOrder[]> {
    return this.request<WorkOrder[]>('/api/work-orders');
  }

  public listAuditEvents(): Promise<AuditEvent[]> {
    return this.request<AuditEvent[]>('/api/audit');
  }

  public createWorkOrder(input: CreateWorkOrderInput): Promise<WorkOrder> {
    return this.request<WorkOrder>('/api/work-orders', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  public async reset(): Promise<void> {
    await this.request<unknown>('/api/admin/reset', { method: 'POST' });
  }
}
