'use client';

import React from 'react';

interface OfflineSyncBannerProps {
  isOnline: boolean;
  onToggleOnline: () => void;
  pendingCount: number;
  onSync: () => void;
}

export const OfflineSyncBanner: React.FC<OfflineSyncBannerProps> = ({
  isOnline,
  onToggleOnline,
  pendingCount,
  onSync,
}) => {
  return (
    <div
      style={{
        backgroundColor: isOnline ? 'var(--bg-secondary)' : 'rgba(245, 158, 11, 0.15)',
        border: isOnline ? '1px solid var(--border-subtle)' : '1px solid var(--color-warning)',
        borderRadius: '8px',
        padding: '0.75rem 1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '0.75rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span
          style={{
            display: 'inline-block',
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            backgroundColor: isOnline ? 'var(--color-success)' : 'var(--color-warning)',
          }}
        />
        <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>
          {isOnline ? 'Cellular / Mesh Gateway Connected' : 'Field Offline Mode (Local Storage Active)'}
        </strong>
        {pendingCount > 0 && (
          <span
            style={{
              backgroundColor: 'var(--color-warning)',
              color: '#000000',
              fontWeight: 700,
              fontSize: '0.7rem',
              padding: '0.15rem 0.5rem',
              borderRadius: '999px',
            }}
          >
            {pendingCount} PENDING SYNC
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          onClick={onToggleOnline}
          style={{
            backgroundColor: 'transparent',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            padding: '0.35rem 0.75rem',
            borderRadius: '4px',
            fontSize: '0.8rem',
            cursor: 'pointer',
          }}
        >
          Simulate: {isOnline ? 'Go Offline' : 'Reconnect Online'}
        </button>

        {pendingCount > 0 && isOnline && (
          <button
            onClick={onSync}
            style={{
              backgroundColor: 'var(--color-brand)',
              color: '#ffffff',
              border: 'none',
              padding: '0.35rem 0.85rem',
              borderRadius: '4px',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Sync Queue Now ({pendingCount})
          </button>
        )}
      </div>
    </div>
  );
};
