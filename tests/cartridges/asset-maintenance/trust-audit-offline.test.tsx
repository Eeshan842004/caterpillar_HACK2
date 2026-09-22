import { describe, it, expect, beforeEach } from 'vitest';
import { SafetyPolicyVerifier } from '@/cartridges/asset-maintenance/domain/services/safety-policy';
import { OfflineSyncService } from '@/cartridges/asset-maintenance/domain/services/offline-sync';
import { InMemoryStorageContainer } from '@/cartridges/asset-maintenance/adapters/in-memory-storage';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { OfflineSyncBanner } from '@/cartridges/asset-maintenance/components/OfflineSyncBanner';

describe('Epic E-06: Trust, Audit, and Offline Behavior', () => {
  let safety: SafetyPolicyVerifier;
  let offlineSync: OfflineSyncService;
  let storage: InMemoryStorageContainer;

  beforeEach(() => {
    safety = new SafetyPolicyVerifier();
    offlineSync = new OfflineSyncService();
    storage = new InMemoryStorageContainer();
  });

  describe('QA-E06-01: Idempotent Offline Queue Synchronization', () => {
    it('prevents duplicate work order creation across multiple sync replays', async () => {
      offlineSync.enqueue({
        asset_id: 'ast_336_001',
        recommendation_id: 'rec_336_001',
        title: 'Emergency Coolant Line Inspection',
        description: 'Overheating remediation',
        priority: 'EMERGENCY',
        status: 'DISPATCHED',
        assigned_technician: 'Marcus Brody',
        approved_by: 'Alex Vance',
        notes: 'Offline draft',
      });

      expect(offlineSync.getQueueLength()).toBe(1);

      // First sync pass
      const firstResult = await offlineSync.syncAll(storage.workOrders, storage.audit);
      expect(firstResult.synced).toBe(1);
      expect(firstResult.skipped).toBe(0);

      const ordersAfterFirst = await storage.workOrders.findAll();
      expect(ordersAfterFirst.length).toBe(1);

      // Second sync pass (replay)
      const secondResult = await offlineSync.syncAll(storage.workOrders, storage.audit);
      expect(secondResult.synced).toBe(0);
      expect(secondResult.skipped).toBe(1);

      // Verify no duplicate order inserted
      const ordersAfterSecond = await storage.workOrders.findAll();
      expect(ordersAfterSecond.length).toBe(1);
    });
  });

  describe('QA-E06-02: Tamper Detection on Audit Records', () => {
    it('verifies pristine audit record and flags tampered payload', () => {
      const auditEvent = {
        id: 'aud_test_001',
        timestamp: '2026-09-22T00:30:00.000Z',
        actor_name: 'Alex Vance',
        actor_role: 'Field Service Supervisor',
        action: 'WORK_ORDER_DISPATCHED' as const,
        target_id: 'wo_001',
        details: 'Authorized work order',
        payload_snapshot: { confidence: 0.94, parts: ['Radiator Hose'] },
      };

      const checksum = safety.generateAuditHash(auditEvent);
      expect(checksum).toBeDefined();
      expect(checksum.length).toBe(64); // SHA-256 hex string

      // Verification on pristine event
      expect(safety.verifyAuditIntegrity(auditEvent, checksum)).toBe(true);

      // Tamper simulation: mutate details or payload
      const tamperedEvent = {
        ...auditEvent,
        details: 'Tampered details: Unauthorized modification',
      };
      expect(safety.verifyAuditIntegrity(tamperedEvent, checksum)).toBe(false);
    });
  });

  describe('QA-E06-03: Safety Policy Rejection of Unconfirmed Action', () => {
    it('rejects work order lacking human approver signature (ADR-0003)', () => {
      const unconfirmedOrder = {
        asset_id: 'ast_336_001',
        title: 'Autonomous Radiator Actuation',
        approved_by: '', // Missing human signature
        approved_at: new Date().toISOString(),
      };

      const result = safety.validateWorkOrder(unconfirmedOrder);
      expect(result.isValid).toBe(false);
      expect(result.violations.some((v) => v.includes('ADR-0003'))).toBe(true);
    });

    it('approves complete, human-verified work order payload', () => {
      const validOrder = {
        asset_id: 'ast_336_001',
        title: 'Emergency Coolant Repair',
        approved_by: 'Alex Vance (Supervisor)',
        approved_at: new Date().toISOString(),
      };

      const result = safety.validateWorkOrder(validOrder);
      expect(result.isValid).toBe(true);
      expect(result.violations.length).toBe(0);
    });
  });

  describe('QA-E06-04: Offline UI State & Sync Indicator', () => {
    it('renders offline connectivity status and pending sync count', () => {
      let isOnline = false;
      const toggle = () => {
        isOnline = !isOnline;
      };
      const syncMock = () => {};

      const { rerender } = render(
        <OfflineSyncBanner
          isOnline={false}
          onToggleOnline={toggle}
          pendingCount={3}
          onSync={syncMock}
        />
      );

      expect(screen.getByText(/Field Offline Mode/i)).toBeInTheDocument();
      expect(screen.getByText(/3 PENDING SYNC/i)).toBeInTheDocument();

      // Rerender as online
      rerender(
        <OfflineSyncBanner
          isOnline={true}
          onToggleOnline={toggle}
          pendingCount={3}
          onSync={syncMock}
        />
      );

      expect(screen.getByText(/Cellular \/ Mesh Gateway Connected/i)).toBeInTheDocument();
      expect(screen.getByText(/Sync Queue Now \(3\)/i)).toBeInTheDocument();
    });
  });
});
