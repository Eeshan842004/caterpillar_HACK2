import { describe, it, expect, beforeEach } from 'vitest';
import { IngestionService } from '@/cartridges/asset-maintenance/domain/services/ingestion';
import { InMemoryStorageContainer } from '@/cartridges/asset-maintenance/adapters/in-memory-storage';

describe('Epic E-03: Ingestion and Storage Profile', () => {
  let ingestion: IngestionService;
  let storage: InMemoryStorageContainer;

  beforeEach(() => {
    ingestion = new IngestionService();
    storage = new InMemoryStorageContainer();
  });

  describe('QA-E03-01: Ingestion Quality Tagging (Physical Boundary)', () => {
    it('flags coolant temperature exceeding physical max as OUT_OF_RANGE', () => {
      const point = ingestion.process({
        asset_id: 'ast_336_001',
        parameter: 'engine_coolant_temp_c',
        value: 195.0, // Exceeds 150°C physical max
        unit: '°C',
        observed_at: new Date().toISOString(),
      });

      expect(point.quality).toBe('OUT_OF_RANGE');
      expect(point.value).toBe(195.0);
      expect(point.ingested_at).toBeDefined();
    });

    it('flags negative oil pressure as OUT_OF_RANGE', () => {
      const point = ingestion.process({
        asset_id: 'ast_336_001',
        parameter: 'engine_oil_pressure_kpa',
        value: -15.0,
        unit: 'kPa',
        observed_at: new Date().toISOString(),
      });

      expect(point.quality).toBe('OUT_OF_RANGE');
    });
  });

  describe('QA-E03-02: Stale Telemetry Detection', () => {
    it('flags readings older than 2 hours as STALE', () => {
      const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString();
      const point = ingestion.process({
        asset_id: 'ast_745_002',
        parameter: 'engine_coolant_temp_c',
        value: 90.0,
        unit: '°C',
        observed_at: sixHoursAgo,
      });

      expect(point.quality).toBe('STALE');
    });

    it('marks recent readings within normal range as GOOD', () => {
      const recent = new Date(Date.now() - 5 * 60 * 1000).toISOString();
      const point = ingestion.process({
        asset_id: 'ast_980_003',
        parameter: 'engine_coolant_temp_c',
        value: 92.0,
        unit: '°C',
        observed_at: recent,
      });

      expect(point.quality).toBe('GOOD');
    });
  });

  describe('QA-E03-03: Repository CRUD and Query Isolation', () => {
    it('manages work order lifecycle through repository interface', async () => {
      const created = await storage.workOrders.create({
        asset_id: 'ast_336_001',
        recommendation_id: 'rec_336_001',
        title: 'Emergency Coolant Line Inspection',
        description: 'Inspect radiator core and coolant hoses for leaks.',
        priority: 'EMERGENCY',
        status: 'DISPATCHED',
        assigned_technician: 'Marcus Brody',
        approved_by: 'Alex Vance',
      });

      expect(created.id).toMatch(/^wo_/);
      expect(created.status).toBe('DISPATCHED');
      expect(created.approved_at).toBeDefined();

      const retrieved = await storage.workOrders.findById(created.id);
      expect(retrieved).not.toBeNull();
      expect(retrieved?.title).toBe('Emergency Coolant Line Inspection');

      // Update status
      const updated = await storage.workOrders.updateStatus(created.id, 'COMPLETED');
      expect(updated?.status).toBe('COMPLETED');
      expect(updated?.completed_at).toBeDefined();
    });

    it('records and retrieves immutable audit events', async () => {
      const event = await storage.audit.record({
        actor_name: 'Alex Vance',
        actor_role: 'Field Service Supervisor',
        action: 'WORK_ORDER_DISPATCHED',
        target_id: 'ast_336_001',
        details: 'Approved emergency work order following SPN 110 alert',
        payload_snapshot: { confidence: 0.94 },
      });

      expect(event.id).toMatch(/^aud_/);
      expect(event.timestamp).toBeDefined();

      const allAudits = await storage.audit.findAll();
      expect(allAudits.some((a) => a.id === event.id)).toBe(true);
    });

    it('queries assets and updates status safely', async () => {
      const asset = await storage.assets.findById('ast_336_001');
      expect(asset).not.toBeNull();
      expect(asset?.model).toBe('336 Hydraulic Excavator');

      const updated = await storage.assets.updateStatus('ast_336_001', 'NOMINAL');
      expect(updated?.status).toBe('NOMINAL');
    });
  });

  describe('QA-E03-04: Deterministic Repository Reset', () => {
    it('restores repository to initial ground-truth fixtures and clears work orders', async () => {
      // Create a work order
      await storage.workOrders.create({
        asset_id: 'ast_336_001',
        recommendation_id: 'rec_temp',
        title: 'Temporary Inspection',
        description: 'Testing reset',
        priority: 'LOW',
        status: 'DRAFT',
        assigned_technician: 'Tester',
        approved_by: 'Tester',
      });

      let orders = await storage.workOrders.findAll();
      expect(orders.length).toBe(1);

      // Mutate asset status
      await storage.assets.updateStatus('ast_336_001', 'OFFLINE');
      const mutatedAsset = await storage.assets.findById('ast_336_001');
      expect(mutatedAsset?.status).toBe('OFFLINE');

      // Perform reset
      storage.reset();

      orders = await storage.workOrders.findAll();
      expect(orders.length).toBe(0);

      const resetAsset = await storage.assets.findById('ast_336_001');
      expect(resetAsset?.status).toBe('CRITICAL'); // Restored to seed value
    });
  });
});
