import { describe, it, expect, beforeEach } from 'vitest';
import { GET as getFleet } from '@/app/api/fleet/route';
import { GET as getAsset } from '@/app/api/assets/[id]/route';
import { GET as getWorkOrders, POST as createWorkOrder } from '@/app/api/work-orders/route';
import { GET as getAudit } from '@/app/api/audit/route';
import { POST as resetAdmin } from '@/app/api/admin/reset/route';
import { NextRequest } from 'next/server';

describe('Epic E-07: Hero-Path Route-Handler Integration', () => {
  beforeEach(async () => {
    // Clean reset before each test
    await resetAdmin();
  });

  describe('QA-E07-01: Full Fleet Query via BFF API', () => {
    it('returns all 4 fleet equipment assets with operating metadata', async () => {
      const response = await getFleet();
      expect(response.status).toBe(200);

      const json = await response.json();
      expect(json.success).toBe(true);
      expect(json.count).toBe(4);
      expect(json.data.some((a: any) => a.id === 'ast_336_001')).toBe(true);
      expect(json.data.some((a: any) => a.id === 'ast_745_002')).toBe(true);
    });
  });

  describe('QA-E07-02: Hero Asset Evaluation via BFF API', () => {
    it('evaluates hero asset ast_336_001 with emergency coolant recommendation and citations', async () => {
      const request = new NextRequest('http://localhost:3000/api/assets/ast_336_001');
      const response = await getAsset(request, { params: { id: 'ast_336_001' } });
      expect(response.status).toBe(200);

      const json = await response.json();
      expect(json.success).toBe(true);

      const { asset, active_faults, recommendation } = json.data;
      expect(asset.id).toBe('ast_336_001');
      expect(asset.status).toBe('CRITICAL');

      // Active DTC fault
      expect(active_faults.some((f: any) => f.spn === 110 && f.fmi === 0)).toBe(true);

      // Recommendation
      expect(recommendation.urgency).toBe('IMMEDIATE');
      expect(recommendation.confidence_score).toBeGreaterThanOrEqual(0.9);
      expect(recommendation.title).toContain('Emergency Coolant System Inspection');
      expect(recommendation.evidence_citations.length).toBeGreaterThan(0);

      const tempCitation = recommendation.evidence_citations.find(
        (c: any) => c.parameter === 'engine_coolant_temp_c'
      );
      expect(tempCitation.observed_value).toBe(108.5);
    });

    it('returns 404 for nonexistent asset ID', async () => {
      const request = new NextRequest('http://localhost:3000/api/assets/unknown_999');
      const response = await getAsset(request, { params: { id: 'unknown_999' } });
      expect(response.status).toBe(404);
    });
  });

  describe('QA-E07-03: Safety Policy Rejection of Anonymous Dispatch', () => {
    it('blocks work order dispatch when human approver signature is missing (ADR-0003)', async () => {
      const invalidPayload = {
        asset_id: 'ast_336_001',
        title: 'Autonomous Coolant Drain',
        priority: 'EMERGENCY',
        approved_by: '', // Missing
      };

      const request = new NextRequest('http://localhost:3000/api/work-orders', {
        method: 'POST',
        body: JSON.stringify(invalidPayload),
      });

      const response = await createWorkOrder(request);
      expect(response.status).toBe(400);

      const json = await response.json();
      expect(json.success).toBe(false);
      expect(json.violations.some((v: string) => v.includes('ADR-0003'))).toBe(true);
    });
  });

  describe('QA-E07-04: Human Authorized Work Order Dispatch & Audit Trail', () => {
    it('creates verified work order and records tamper-evident audit event with SHA-256 hash', async () => {
      const validPayload = {
        asset_id: 'ast_336_001',
        recommendation_id: 'rec_coolant_ast_336_001',
        title: 'Emergency Coolant Circuit Repair: CAT-336-HEX-8821',
        description: 'Authorized radiator inspection following SPN 110 FMI 0 alert.',
        priority: 'EMERGENCY',
        assigned_technician: 'Marcus Brody',
        approved_by: 'Alex Vance (Field Service Supervisor)',
        notes: 'Priority dispatch authorized.',
      };

      const request = new NextRequest('http://localhost:3000/api/work-orders', {
        method: 'POST',
        body: JSON.stringify(validPayload),
      });

      const response = await createWorkOrder(request);
      expect(response.status).toBe(201);

      const json = await response.json();
      expect(json.success).toBe(true);
      expect(json.data.id).toMatch(/^wo_/);
      expect(json.audit_checksum).toBeDefined();
      expect(json.audit_checksum.length).toBe(64); // SHA-256 hash

      // Verify work order appears in GET /api/work-orders
      const ordersResponse = await getWorkOrders();
      const ordersJson = await ordersResponse.json();
      expect(ordersJson.count).toBe(1);
      expect(ordersJson.data[0].id).toBe(json.data.id);

      // Verify audit event appears in GET /api/audit
      const auditResponse = await getAudit();
      const auditJson = await auditResponse.json();
      expect(auditJson.data.some((a: any) => a.target_id === json.data.id)).toBe(true);
    });

    it('returns the original work order for a repeated idempotency key', async () => {
      const payload = {
        asset_id: 'ast_336_001',
        recommendation_id: 'rec_coolant_ast_336_001',
        title: 'Idempotent Coolant Inspection',
        priority: 'HIGH',
        assigned_technician: 'Marcus Brody',
        approved_by: 'Alex Vance',
        idempotency_key: 'idemp_test_replay_001',
      };

      const first = await createWorkOrder(
        new NextRequest('http://localhost:3000/api/work-orders', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
      );
      const second = await createWorkOrder(
        new NextRequest('http://localhost:3000/api/work-orders', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
      );

      const firstJson = await first.json();
      const secondJson = await second.json();
      expect(secondJson.replayed).toBe(true);
      expect(secondJson.data.id).toBe(firstJson.data.id);

      const ordersJson = await (await getWorkOrders()).json();
      expect(ordersJson.count).toBe(1);

      const auditJson = await (await getAudit()).json();
      const matchingAudits = auditJson.data.filter(
        (event: any) => event.target_id === firstJson.data.id
      );
      expect(matchingAudits).toHaveLength(1);
    });
  });

  describe('QA-E07-05: Reset State API Execution', () => {
    it('restores repository state to initial ground-truth fixtures and clears orders', async () => {
      // Dispatch an order first
      const request = new NextRequest('http://localhost:3000/api/work-orders', {
        method: 'POST',
        body: JSON.stringify({
          asset_id: 'ast_336_001',
          title: 'Pre-Reset Order',
          approved_by: 'Alex Vance',
        }),
      });
      await createWorkOrder(request);

      let ordersResponse = await getWorkOrders();
      let ordersJson = await ordersResponse.json();
      expect(ordersJson.count).toBe(1);

      // Call Reset API
      const resetResponse = await resetAdmin();
      expect(resetResponse.status).toBe(200);

      const resetJson = await resetResponse.json();
      expect(resetJson.success).toBe(true);

      // Verify orders cleared
      ordersResponse = await getWorkOrders();
      ordersJson = await ordersResponse.json();
      expect(ordersJson.count).toBe(0);
    });
  });
});
