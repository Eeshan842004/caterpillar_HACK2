'use client';

import React from 'react';
import { WorkOrder, AuditEvent } from '@/cartridges/asset-maintenance/domain/types';

interface AuditLogViewProps {
  workOrders: WorkOrder[];
  auditEvents: AuditEvent[];
}

export const AuditLogView: React.FC<AuditLogViewProps> = ({
  workOrders,
  auditEvents,
}) => {
  return (
    <section aria-label="Operations History and Audit Trail" style={{ marginTop: '2rem' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
        {/* Dispatched Work Orders */}
        <div
          style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Dispatched Work Orders ({workOrders.length})
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Verified Dispatches</span>
          </div>

          {workOrders.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No work orders dispatched in this session.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {workOrders.map((wo) => (
                <div
                  key={wo.id}
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '6px',
                    padding: '0.75rem 1rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{wo.title}</strong>
                    <span
                      style={{
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        color: 'var(--color-success)',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '0.15rem 0.4rem',
                        borderRadius: '4px',
                      }}
                    >
                      {wo.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.35rem' }}>
                    Assigned: {wo.assigned_technician} | Approved by: {wo.approved_by}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem', fontFamily: 'var(--font-mono)' }}>
                    Dispatched: {wo.approved_at}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Immutable Audit Log */}
        <div
          style={{
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Immutable Compliance Audit Trail ({auditEvents.length})
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-brand)', fontFamily: 'var(--font-mono)' }}>
              🔒 Tamper-Evident
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '280px', overflowY: 'auto' }}>
            {auditEvents.map((aud) => (
              <div
                key={aud.id}
                style={{
                  fontSize: '0.75rem',
                  backgroundColor: 'var(--bg-primary)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '0.5rem 0.75rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  <span>{aud.timestamp}</span>
                  <strong style={{ color: 'var(--color-brand)' }}>{aud.action}</strong>
                </div>
                <div style={{ color: 'var(--text-primary)', marginTop: '0.2rem', fontWeight: 500 }}>
                  {aud.actor_name} ({aud.actor_role})
                </div>
                <div style={{ color: 'var(--text-secondary)', marginTop: '0.1rem' }}>{aud.details}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
