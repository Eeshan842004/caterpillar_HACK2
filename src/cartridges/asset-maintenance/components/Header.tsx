'use client';

import React from 'react';
import { DEMO_PERSONA } from '@/cartridges/asset-maintenance/domain/constants';

interface HeaderProps {
  onReset: () => void;
  isResetting?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onReset, isResetting }) => {
  return (
    <header
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        backgroundColor: 'var(--bg-secondary)',
        padding: '1rem 1.5rem',
        marginBottom: '1.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.35rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
              Industrial Asset Operations Workspace
            </h1>
            <span
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                color: 'var(--color-danger)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                padding: '0.2rem 0.6rem',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Advisory Decision Support
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.25rem' }}>
            Site: {DEMO_PERSONA.site} | Timezone: Asia/Calcutta | User:{' '}
            <strong style={{ color: 'var(--text-primary)' }}>{DEMO_PERSONA.name}</strong> ({DEMO_PERSONA.role})
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span
            style={{
              fontSize: '0.8rem',
              color: 'var(--color-warning)',
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              padding: '0.35rem 0.75rem',
              borderRadius: '4px',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              fontWeight: 500,
            }}
          >
            SYNTHETIC DEMO DATA
          </span>

          <button
            onClick={onReset}
            disabled={isResetting}
            aria-label="Reset Demo State"
            style={{
              backgroundColor: 'var(--bg-tertiary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              transition: 'background-color 0.2s',
            }}
          >
            {isResetting ? 'Resetting...' : '↺ Reset Demo State'}
          </button>
        </div>
      </div>
    </header>
  );
};
