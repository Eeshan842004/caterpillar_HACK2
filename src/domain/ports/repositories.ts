import {
  Asset,
  TelemetryPoint,
  DiagnosticFault,
  WorkOrder,
  AuditEvent,
  OperatingStatus,
  WorkOrderStatus,
} from '../types';

export interface IAssetRepository {
  findAll(): Promise<Asset[]>;
  findById(id: string): Promise<Asset | null>;
  updateStatus(id: string, status: OperatingStatus): Promise<Asset | null>;
}

export interface ITelemetryRepository {
  ingest(point: TelemetryPoint): Promise<TelemetryPoint>;
  findByAsset(assetId: string): Promise<TelemetryPoint[]>;
  findByAssetAndParameter(assetId: string, parameter: string): Promise<TelemetryPoint[]>;
  getLatestByAsset(assetId: string): Promise<Record<string, TelemetryPoint>>;
}

export interface IFaultRepository {
  findAll(): Promise<DiagnosticFault[]>;
  findByAsset(assetId: string): Promise<DiagnosticFault[]>;
  findActiveByAsset(assetId: string): Promise<DiagnosticFault[]>;
  acknowledge(id: string): Promise<DiagnosticFault | null>;
}

export interface IWorkOrderRepository {
  findAll(): Promise<WorkOrder[]>;
  findById(id: string): Promise<WorkOrder | null>;
  findByAsset(assetId: string): Promise<WorkOrder[]>;
  create(order: Omit<WorkOrder, 'id' | 'approved_at'>): Promise<WorkOrder>;
  updateStatus(id: string, status: WorkOrderStatus): Promise<WorkOrder | null>;
}

export interface IAuditRepository {
  record(event: Omit<AuditEvent, 'id' | 'timestamp'>): Promise<AuditEvent>;
  findAll(): Promise<AuditEvent[]>;
  findByTarget(targetId: string): Promise<AuditEvent[]>;
}
