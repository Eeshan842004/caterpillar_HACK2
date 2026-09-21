'use client';

import React from 'react';
import { Asset, OperatingStatus } from '@/domain/types';

interface AssetSelectorProps {
  assets: Asset[];
  selectedAssetId: string;
  onSelectAsset: (assetId: string) => void;
}

export const AssetSelector: React.FC<AssetSelectorProps> = ({
  assets,
  selectedAssetId,
  onSelectAsset,
}) => {
  const getStatusColor = (status: OperatingStatus) => {
    switch (status) {
      case 'CRITICAL':
        return { bg: 'rgba(239, 68, 68, 0.2)', text: 'var(--color-danger)', border: 'var(--color-danger)' };
      case 'WARNING':
        return { bg: 'rgba(245, 158, 11, 0.2)', text: 'var(--color-warning)', border: 'var(--color-warning)' };
      case 'NOMINAL':
        return { bg: 'rgba(16, 185, 129, 0.2)', text: 'var(--color-success)', border: 'var(--color-success)' };
      default:
        return { bg: 'rgba(100, 116, 139, 0.2)', text: 'var(--color-neutral)', border: 'var(--border-subtle)' };
    }
  };

  return (
    <section aria-label="Fleet Equipment Selection" style={{ marginBottom: '1.5rem' }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Connected Equipment Fleet ({assets.length} Units)
      </h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
        }}
      >
        {assets.map((asset) => {
          const isSelected = asset.id === selectedAssetId;
          const statusStyle = getStatusColor(asset.status);

          return (
            <button
              key={asset.id}
              onClick={() => onSelectAsset(asset.id)}
              aria-pressed={isSelected}
              style={{
                backgroundColor: isSelected ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
                border: isSelected ? '2px solid var(--border-focus)' : '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '1rem',
                textAlign: 'left',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {asset.serial_number}
                </span>
                <span
                  style={{
                    backgroundColor: statusStyle.bg,
                    color: statusStyle.text,
                    border: `1px solid ${statusStyle.border}`,
                    padding: '0.15rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                  }}
                >
                  {asset.status}
                </span>
              </div>

              <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>
                {asset.model}
              </strong>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                <span>Hours: {asset.engine_hours.toFixed(1)} h</span>
                <span>Fuel: {asset.fuel_level_pct}%</span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
};
