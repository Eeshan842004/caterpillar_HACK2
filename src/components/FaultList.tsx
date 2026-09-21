'use client';

import React from 'react';
import { DiagnosticFault, FaultSeverity } from '@/domain/types';

interface FaultListProps {
  faults: DiagnosticFault[];
}

export const FaultList: React.FC<FaultListProps> = ({ faults }) => {
  const getSeverityStyle = (severity: FaultSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return { bg: 'rgba(239, 68, 68, 0.2)', text: 'var(--color-danger)' };
      case 'HIGH':
      case 'MEDIUM':
        return { bg: 'rgba(245, 158, 11, 0.2)', text: 'var(--color-warning)' };
      default:
        return { bg: 'rgba(56, 189, 248, 0.2)', text: 'var(--color-brand)' };
    }
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-secondary)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
      }}
    >
      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
        Active Diagnostic Faults ({faults.length})
      </h3>

      {faults.length === 0 ? (
        <div style={{ color: 'var(--color-success)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>✓</span> Zero active Diagnostic Trouble Codes (DTCs). System clear.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {faults.map((fault) => {
            const sevStyle = getSeverityStyle(fault.severity);
            return (
              <div
                key={fault.id}
                style={{
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  padding: '0.75rem 1rem',
                  backgroundColor: 'var(--bg-primary)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                    }}
                  >
                    {fault.raw_code}
                  </span>
                  <span
                    style={{
                      backgroundColor: sevStyle.bg,
                      color: sevStyle.text,
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      padding: '0.15rem 0.5rem',
                      borderRadius: '4px',
                    }}
                  >
                    {fault.severity}
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  {fault.standard_description}
                </p>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem', fontStyle: 'italic' }}>
                  Diagnostic Interpretation: {fault.source_interpretation}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
