'use client';

import React, { useState } from 'react';
import { Recommendation, Asset } from '@/domain/types';
import { DEMO_PERSONA } from '@/domain/constants';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: { technician: string; notes: string }) => void;
  recommendation: Recommendation;
  asset: Asset;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  recommendation,
  asset,
}) => {
  const [technician, setTechnician] = useState('Marcus Brody (Lead Hydraulic Tech)');
  const [notes, setNotes] = useState('Immediate dispatch authorized following automated temperature anomaly triage.');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConfirm({ technician, notes });
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '2px solid var(--border-focus)',
          borderRadius: '10px',
          maxWidth: '560px',
          width: '100%',
          padding: '1.75rem',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 id="modal-title" style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Human Authorization: Dispatch Work Order
          </h2>
          <button
            onClick={onClose}
            aria-label="Close modal"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '1.25rem',
              cursor: 'pointer',
            }}
          >
            ✕
          </button>
        </div>

        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '6px',
            padding: '0.75rem 1rem',
            marginBottom: '1.25rem',
          }}
        >
          <p style={{ color: 'var(--color-danger)', fontSize: '0.85rem', fontWeight: 600 }}>
            ⚠ SAFETY COMPLIANCE GATE (ADR-0003)
          </p>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.2rem' }}>
            This system provides advisory diagnostic support. An authorized human supervisor must explicitly verify evidence and authorize maintenance dispatch.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
              Target Asset & Location
            </label>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600 }}>
              {asset.model} ({asset.serial_number}) — {asset.site_name}
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
              Work Order Title & Priority
            </label>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 600 }}>
              {recommendation.suggested_work_order.title} ({recommendation.suggested_work_order.priority})
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
              Required Replacement Parts
            </label>
            <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
              {recommendation.suggested_work_order.required_parts.map((part, idx) => (
                <li key={idx}>{part}</li>
              ))}
            </ul>
          </div>

          <div>
            <label htmlFor="tech-assign" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
              Assign Field Technician
            </label>
            <input
              id="tech-assign"
              type="text"
              value={technician}
              onChange={(e) => setTechnician(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                fontSize: '0.85rem',
              }}
            />
          </div>

          <div>
            <label htmlFor="notes-field" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '0.25rem' }}>
              Supervisor Authorization Notes
            </label>
            <textarea
              id="notes-field"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              style={{
                width: '100%',
                padding: '0.5rem',
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                color: 'var(--text-primary)',
                fontSize: '0.85rem',
                resize: 'none',
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                backgroundColor: 'transparent',
                color: 'var(--text-secondary)',
                border: '1px solid var(--border-subtle)',
                padding: '0.6rem 1.2rem',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                backgroundColor: 'var(--color-success)',
                color: '#ffffff',
                border: 'none',
                padding: '0.6rem 1.25rem',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Authorize & Dispatch Work Order
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
