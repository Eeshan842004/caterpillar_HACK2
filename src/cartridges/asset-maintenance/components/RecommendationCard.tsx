'use client';

import React from 'react';
import { Recommendation } from '@/cartridges/asset-maintenance/domain/types';

interface RecommendationCardProps {
  recommendation: Recommendation | null;
  onOpenConfirmation: () => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onOpenConfirmation,
}) => {
  if (!recommendation) {
    return (
      <div
        style={{
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          padding: '1.5rem',
          textAlign: 'center',
          color: 'var(--text-muted)',
        }}
      >
        No active recommendation for this asset.
      </div>
    );
  }

  const isEmergency = recommendation.urgency === 'IMMEDIATE';
  const confidencePct = Math.round(recommendation.confidence_score * 100);

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-secondary)',
        border: isEmergency ? '2px solid var(--color-danger)' : '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '1.25rem',
        marginBottom: '1.5rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <span
            style={{
              backgroundColor: isEmergency ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.2)',
              color: isEmergency ? 'var(--color-danger)' : 'var(--color-brand)',
              fontSize: '0.75rem',
              fontWeight: 700,
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {recommendation.urgency} ADVISORY
          </span>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.5rem' }}>
            {recommendation.title}
          </h3>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>DIAGNOSTIC CONFIDENCE</span>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: confidencePct > 80 ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {confidencePct}%
          </div>
        </div>
      </div>

      <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.75rem', lineHeight: 1.6 }}>
        {recommendation.diagnostic_summary}
      </p>

      {/* Evidence Citations Table */}
      <div style={{ marginTop: '1rem' }}>
        <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
          Cited Sensor Evidence & Lineage
        </h4>
        <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {recommendation.evidence_citations.map((c, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.8rem',
                backgroundColor: 'var(--bg-primary)',
                padding: '0.4rem 0.75rem',
                borderRadius: '4px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-brand)' }}>{c.parameter}</span>
              <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                Observed: {c.observed_value} {c.unit} (Limit: {c.threshold_value} {c.unit})
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Action & Dispatch Trigger */}
      <div
        style={{
          marginTop: '1.25rem',
          paddingTop: '1rem',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ACTION PROTOCOL:</span>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>
            {recommendation.recommended_action}
          </p>
        </div>

        {recommendation.urgency !== 'OBSERVE' && (
          <button
            onClick={onOpenConfirmation}
            style={{
              backgroundColor: isEmergency ? 'var(--color-danger)' : 'var(--color-brand)',
              color: '#ffffff',
              border: 'none',
              padding: '0.65rem 1.25rem',
              borderRadius: '6px',
              fontSize: '0.9rem',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            Review & Confirm Work Order →
          </button>
        )}
      </div>
    </div>
  );
};
