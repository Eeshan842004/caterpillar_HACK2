'use client';

import React, { useState, useMemo } from 'react';
import {
  Asset,
  TelemetryPoint,
  DiagnosticFault,
  WorkOrder,
  AuditEvent,
} from '@/domain/types';
import {
  loadSeedAssets,
  loadSeedFaults,
  loadSeedTelemetry,
} from '@/domain/fixtures/loader';
import { RecommendationEngine } from '@/domain/services/recommendation-engine';
import { OfflineSyncService } from '@/domain/services/offline-sync';
import { DEMO_PERSONA } from '@/domain/constants';
import { Header } from './Header';
import { AssetSelector } from './AssetSelector';
import { TelemetryChart } from './TelemetryChart';
import { FaultList } from './FaultList';
import { RecommendationCard } from './RecommendationCard';
import { ConfirmationModal } from './ConfirmationModal';
import { AuditLogView } from './AuditLogView';
import { OfflineSyncBanner } from './OfflineSyncBanner';

export const Workspace: React.FC = () => {
  const [assets, setAssets] = useState<Asset[]>(() => loadSeedAssets());
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>(() => loadSeedTelemetry());
  const [faults, setFaults] = useState<DiagnosticFault[]>(() => loadSeedFaults());
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([
    {
      id: 'aud_init_001',
      timestamp: new Date().toISOString(),
      actor_name: 'System',
      actor_role: 'Deterministic Seed Loader',
      action: 'SYSTEM_RESET',
      target_id: 'fleet',
      details: 'Initialized with seed_cat_2026_v1 baseline fixtures',
      payload_snapshot: { version: 'seed_cat_2026_v1' },
    },
  ]);

  const [selectedAssetId, setSelectedAssetId] = useState<string>('ast_336_001');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [isOnline, setIsOnline] = useState<boolean>(true);

  const engine = useMemo(() => new RecommendationEngine(), []);
  const syncService = useMemo(() => new OfflineSyncService(), []);
  const [pendingSyncCount, setPendingSyncCount] = useState<number>(0);

  // Active Asset
  const selectedAsset = useMemo(
    () => assets.find((a) => a.id === selectedAssetId) || assets[0],
    [assets, selectedAssetId]
  );

  // Active Asset Telemetry & Faults
  const assetTelemetry = useMemo(
    () => telemetry.filter((t) => t.asset_id === selectedAssetId),
    [telemetry, selectedAssetId]
  );

  const assetFaults = useMemo(
    () => faults.filter((f) => f.asset_id === selectedAssetId && f.is_active),
    [faults, selectedAssetId]
  );

  // Latest telemetry lookup for recommendation engine
  const latestTelemetryRecord = useMemo(() => {
    const record: Record<string, TelemetryPoint> = {};
    for (const t of assetTelemetry) {
      if (!record[t.parameter] || new Date(t.observed_at) > new Date(record[t.parameter].observed_at)) {
        record[t.parameter] = t;
      }
    }
    return record;
  }, [assetTelemetry]);

  // Dynamic Recommendation
  const currentRecommendation = useMemo(() => {
    if (!selectedAsset) return null;
    return engine.evaluate(selectedAsset, assetFaults, latestTelemetryRecord);
  }, [engine, selectedAsset, assetFaults, latestTelemetryRecord]);

  // Work Order Confirmation Handler
  const handleConfirmWorkOrder = (data: { technician: string; notes: string }) => {
    if (!currentRecommendation || !selectedAsset) return;

    if (!isOnline) {
      // Offline mode: Enqueue action locally
      syncService.enqueue({
        asset_id: selectedAsset.id,
        recommendation_id: currentRecommendation.id,
        title: currentRecommendation.suggested_work_order.title,
        description: currentRecommendation.diagnostic_summary,
        priority: currentRecommendation.suggested_work_order.priority,
        status: 'DISPATCHED',
        assigned_technician: data.technician,
        approved_by: `${DEMO_PERSONA.name} (${DEMO_PERSONA.role})`,
        notes: `[OFFLINE DRAFT] ${data.notes}`,
      });
      setPendingSyncCount(syncService.getQueueLength());
      setIsModalOpen(false);
      return;
    }

    const newOrder: WorkOrder = {
      id: `wo_${Date.now()}`,
      asset_id: selectedAsset.id,
      recommendation_id: currentRecommendation.id,
      title: currentRecommendation.suggested_work_order.title,
      description: currentRecommendation.diagnostic_summary,
      priority: currentRecommendation.suggested_work_order.priority,
      status: 'DISPATCHED',
      assigned_technician: data.technician,
      approved_by: `${DEMO_PERSONA.name} (${DEMO_PERSONA.role})`,
      approved_at: new Date().toISOString(),
      notes: data.notes,
    };

    const newAuditEvent: AuditEvent = {
      id: `aud_${Date.now()}`,
      timestamp: new Date().toISOString(),
      actor_name: DEMO_PERSONA.name,
      actor_role: DEMO_PERSONA.role,
      action: 'WORK_ORDER_DISPATCHED',
      target_id: newOrder.id,
      details: `Authorized dispatch for ${selectedAsset.model} (${selectedAsset.serial_number}): ${newOrder.title}`,
      payload_snapshot: {
        asset_id: selectedAsset.id,
        fault_id: currentRecommendation.fault_id,
        confidence: currentRecommendation.confidence_score,
        technician: data.technician,
      },
    };

    setWorkOrders((prev) => [newOrder, ...prev]);
    setAuditEvents((prev) => [newAuditEvent, ...prev]);
    setIsModalOpen(false);
  };

  // Reconcile Offline Queue
  const handleSyncQueue = () => {
    const pending = syncService.getPendingQueue();
    const newOrders: WorkOrder[] = [];
    const newAudits: AuditEvent[] = [];

    for (const item of pending) {
      const order: WorkOrder = {
        ...item.payload,
        id: `wo_synced_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        approved_at: new Date().toISOString(),
      };
      newOrders.push(order);

      newAudits.push({
        id: `aud_sync_${Date.now()}`,
        timestamp: new Date().toISOString(),
        actor_name: item.payload.approved_by,
        actor_role: 'Field Supervisor (Synced Replay)',
        action: 'WORK_ORDER_DISPATCHED',
        target_id: order.id,
        details: `Reconciled offline work order: ${order.title} [Idempotency: ${item.idempotency_key}]`,
        payload_snapshot: { idempotency_key: item.idempotency_key },
      });
    }

    syncService.clear();
    setPendingSyncCount(0);
    setWorkOrders((prev) => [...newOrders, ...prev]);
    setAuditEvents((prev) => [...newAudits, ...prev]);
  };

  // Reset State Handler (Deterministic Replay)
  const handleResetDemo = () => {
    setIsResetting(true);
    syncService.clear();
    setPendingSyncCount(0);
    setIsOnline(true);

    setTimeout(() => {
      setAssets(loadSeedAssets());
      setTelemetry(loadSeedTelemetry());
      setFaults(loadSeedFaults());
      setWorkOrders([]);
      setAuditEvents([
        {
          id: `aud_reset_${Date.now()}`,
          timestamp: new Date().toISOString(),
          actor_name: DEMO_PERSONA.name,
          actor_role: DEMO_PERSONA.role,
          action: 'SYSTEM_RESET',
          target_id: 'all',
          details: 'Demonstration environment reset to pristine ground-truth fixtures',
          payload_snapshot: { version: 'seed_cat_2026_v1' },
        },
      ]);
      setSelectedAssetId('ast_336_001');
      setIsResetting(false);
    }, 150);
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-primary)', paddingBottom: '3rem' }}>
      <Header onReset={handleResetDemo} isResetting={isResetting} />

      <main style={{ maxWidth: '1440px', margin: '0 auto', padding: '0 1.5rem' }}>
        {/* Offline Connectivity Banner */}
        <OfflineSyncBanner
          isOnline={isOnline}
          onToggleOnline={() => setIsOnline((prev) => !prev)}
          pendingCount={pendingSyncCount}
          onSync={handleSyncQueue}
        />

        {/* Fleet Equipment Cards */}
        <AssetSelector
          assets={assets}
          selectedAssetId={selectedAssetId}
          onSelectAsset={setSelectedAssetId}
        />

        {/* Selected Asset Header Detail */}
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
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>SELECTED ASSET WORKSPACE</span>
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

        {/* Split Grid: Telemetry & Faults | Advisory Recommendation */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
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

        {/* Audit Log & Work Orders */}
        <AuditLogView workOrders={workOrders} auditEvents={auditEvents} />

        {/* Confirmation Modal */}
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
