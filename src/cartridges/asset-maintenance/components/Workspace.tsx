'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import type {
  Asset,
  AuditEvent,
  WorkOrder,
} from '@/cartridges/asset-maintenance/domain/types';
import { OfflineSyncService } from '@/cartridges/asset-maintenance/domain/services/offline-sync';
import { DEMO_PERSONA } from '@/cartridges/asset-maintenance/domain/constants';
import {
  type AssetMaintenanceClient,
  HttpAssetMaintenanceClient,
} from '@/cartridges/asset-maintenance/client/api-client';
import { Header } from './Header';
import { AssetSelector } from './AssetSelector';
import { TelemetryChart } from './TelemetryChart';
import { FaultList } from './FaultList';
import { RecommendationCard } from './RecommendationCard';
import { ConfirmationModal } from './ConfirmationModal';
import { AuditLogView } from './AuditLogView';
import { OfflineSyncBanner } from './OfflineSyncBanner';

export interface WorkspaceProps {
  client?: AssetMaintenanceClient;
}

export const Workspace: React.FC<WorkspaceProps> = ({ client }) => {
  const api = useMemo(() => client ?? new HttpAssetMaintenanceClient(), [client]);
  const syncService = useMemo(() => new OfflineSyncService(), []);

  const [assets, setAssets] = useState<Asset[]>([]);
  const [selectedAssetId, setSelectedAssetId] = useState('');
  const [assetDetail, setAssetDetail] = useState<Awaited<
    ReturnType<AssetMaintenanceClient['getAsset']>
  > | null>(null);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isOnline, setIsOnline] = useState(true);
  const [pendingSyncCount, setPendingSyncCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const refreshLists = useCallback(async () => {
    const [nextAssets, nextOrders, nextAudits] = await Promise.all([
      api.listAssets(),
      api.listWorkOrders(),
      api.listAuditEvents(),
    ]);
    setAssets(nextAssets);
    setWorkOrders(nextOrders);
    setAuditEvents(nextAudits);
    setSelectedAssetId((current) => {
      if (current && nextAssets.some((asset) => asset.id === current)) return current;
      return nextAssets.find((asset) => asset.id === 'ast_336_001')?.id ?? nextAssets[0]?.id ?? '';
    });
  }, [api]);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    refreshLists()
      .catch((cause) => {
        if (active) {
          setError(cause instanceof Error ? cause.message : 'Failed to load workspace');
        }
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [refreshLists]);

  useEffect(() => {
    if (!selectedAssetId) {
      setAssetDetail(null);
      return;
    }

    let active = true;
    api
      .getAsset(selectedAssetId)
      .then((detail) => {
        if (active) {
          setAssetDetail(detail);
          setError(null);
        }
      })
      .catch((cause) => {
        if (active) {
          setError(cause instanceof Error ? cause.message : 'Failed to load asset detail');
        }
      });

    return () => {
      active = false;
    };
  }, [api, selectedAssetId]);

  const selectedAsset =
    assetDetail?.asset ?? assets.find((asset) => asset.id === selectedAssetId) ?? assets[0];
  const assetTelemetry = assetDetail?.telemetry_history ?? [];
  const assetFaults = assetDetail?.active_faults ?? [];
  const currentRecommendation = assetDetail?.recommendation ?? null;

  const createInput = (
    data: { technician: string; notes: string },
    idempotencyKey?: string
  ) => {
    if (!selectedAsset || !currentRecommendation) return null;

    return {
      asset_id: selectedAsset.id,
      recommendation_id: currentRecommendation.id,
      title: currentRecommendation.suggested_work_order.title,
      description: currentRecommendation.diagnostic_summary,
      priority: currentRecommendation.suggested_work_order.priority,
      assigned_technician: data.technician,
      approved_by: `${DEMO_PERSONA.name} (${DEMO_PERSONA.role})`,
      notes: data.notes,
      idempotency_key: idempotencyKey,
    };
  };

  const handleConfirmWorkOrder = async (data: { technician: string; notes: string }) => {
    const input = createInput(data);
    if (!input) return;

    if (!isOnline) {
      syncService.enqueue({
        ...input,
        status: 'DRAFT',
        notes: `[OFFLINE DRAFT] ${input.notes ?? ''}`,
      });
      setPendingSyncCount(syncService.getQueueLength());
      setIsModalOpen(false);
      return;
    }

    try {
      await api.createWorkOrder(input);
      await refreshLists();
      setIsModalOpen(false);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to dispatch work order');
    }
  };

  const handleSyncQueue = async () => {
    const result = await syncService.syncWith(async (payload, idempotencyKey) => {
      await api.createWorkOrder({
        asset_id: payload.asset_id,
        recommendation_id: payload.recommendation_id,
        title: payload.title,
        description: payload.description,
        priority: payload.priority,
        assigned_technician: payload.assigned_technician,
        approved_by: payload.approved_by,
        notes: payload.notes,
        idempotency_key: idempotencyKey,
      });
    });

    setPendingSyncCount(syncService.getQueueLength());
    await refreshLists();

    if (result.failed > 0) {
      setError(`${result.failed} offline action(s) could not be synchronized`);
    } else {
      setError(null);
    }
  };

  const handleResetDemo = async () => {
    setIsResetting(true);
    setError(null);
    try {
      await api.reset();
      syncService.clear();
      setPendingSyncCount(0);
      setIsOnline(true);
      setSelectedAssetId('ast_336_001');
      await refreshLists();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Failed to reset demo state');
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-primary)', paddingBottom: '3rem' }}>
      <Header onReset={handleResetDemo} isResetting={isResetting} />

      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '0 1.5rem' }}>
        {error && (
          <div role="alert" style={{ margin: '1rem 0', color: 'var(--status-critical)' }}>
            {error}
          </div>
        )}

        {isLoading && <p aria-live="polite">Loading reference workspace…</p>}

        <OfflineSyncBanner
          isOnline={isOnline}
          onToggleOnline={() => setIsOnline((previous) => !previous)}
          pendingCount={pendingSyncCount}
          onSync={handleSyncQueue}
        />

        <AssetSelector
          assets={assets}
          selectedAssetId={selectedAssetId}
          onSelectAsset={setSelectedAssetId}
        />

        {selectedAsset && (
          <div
            style={{
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '1rem 1.5rem',
              marginBottom: '1.5rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
            }}
          >
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                SELECTED ASSET WORKSPACE
              </span>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {selectedAsset.model} ({selectedAsset.serial_number})
              </h2>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>SITE:</span>{' '}
                <strong>{selectedAsset.site_name}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>OPERATING HOURS:</span>{' '}
                <strong>{selectedAsset.engine_hours.toFixed(1)} h</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>FUEL:</span>{' '}
                <strong>{selectedAsset.fuel_level_pct}%</strong>
              </div>
            </div>
          </div>
        )}

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))',
            gap: '1.5rem',
          }}
        >
          <div>
            <TelemetryChart
              telemetryPoints={assetTelemetry}
              parameterName="engine_coolant_temp_c"
            />
            <FaultList faults={assetFaults} />
          </div>

          <div>
            <RecommendationCard
              recommendation={currentRecommendation}
              onOpenConfirmation={() => setIsModalOpen(true)}
            />
          </div>
        </div>

        <AuditLogView workOrders={workOrders} auditEvents={auditEvents} />

        {currentRecommendation && selectedAsset && (
          <ConfirmationModal
            isOpen={isModalOpen}
            onClose={() => setIsModalOpen(false)}
            onConfirm={handleConfirmWorkOrder}
            recommendation={currentRecommendation}
            asset={selectedAsset}
          />
        )}
      </main>
    </div>
  );
};
