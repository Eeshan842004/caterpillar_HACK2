import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  AssetMaintenanceApiError,
  HttpAssetMaintenanceClient,
} from '@/cartridges/asset-maintenance/client/api-client';

describe('Asset-maintenance HTTP client', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('uses an uncached read so mutations are visible to the workspace', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true, data: [] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    const client = new HttpAssetMaintenanceClient('https://starter.invalid');
    await client.listAuditEvents();

    expect(fetchMock).toHaveBeenCalledWith(
      'https://starter.invalid/api/audit',
      expect.objectContaining({ cache: 'no-store' })
    );
  });

  it('surfaces API policy violations as a typed error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: false,
            error: 'Safety Policy Gate Failure',
            violations: ['Human approval is required'],
          }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        )
      )
    );

    const client = new HttpAssetMaintenanceClient();

    await expect(
      client.createWorkOrder({
        asset_id: 'ast_001',
        recommendation_id: 'rec_001',
        title: 'Inspect system',
        description: 'Reference action',
        priority: 'HIGH',
        assigned_technician: 'Technician',
        approved_by: '',
      })
    ).rejects.toEqual(
      expect.objectContaining<Partial<AssetMaintenanceApiError>>({
        message: 'Safety Policy Gate Failure',
        status: 400,
        violations: ['Human approval is required'],
      })
    );
  });
});
