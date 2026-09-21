import { describe, it, expect, beforeEach } from 'vitest';
import { RecommendationEngine } from '@/domain/services/recommendation-engine';
import {
  loadSeedAssets,
  loadSeedFaults,
  loadSeedTelemetry,
} from '@/domain/fixtures/loader';

describe('Epic E-04: Baseline Analytics and Recommendations', () => {
  let engine: RecommendationEngine;

  beforeEach(() => {
    engine = new RecommendationEngine();
  });

  describe('QA-E04-01: Hero Overheating Anomaly Evaluation', () => {
    it('generates high-confidence emergency recommendation for asset ast_336_001', () => {
      const assets = loadSeedAssets();
      const heroAsset = assets.find((a) => a.id === 'ast_336_001')!;
      const faults = loadSeedFaults().filter((f) => f.asset_id === heroAsset.id);
      const telemetry = loadSeedTelemetry().filter((t) => t.asset_id === heroAsset.id);

      const latestTelemetry: Record<string, any> = {};
      for (const t of telemetry) {
        latestTelemetry[t.parameter] = t;
      }

      const recommendation = engine.evaluate(heroAsset, faults, latestTelemetry);

      expect(recommendation.urgency).toBe('IMMEDIATE');
      expect(recommendation.confidence_score).toBeGreaterThanOrEqual(0.9);
      expect(recommendation.title).toContain('Emergency Coolant System Inspection');
      expect(recommendation.suggested_work_order.priority).toBe('EMERGENCY');
      expect(recommendation.suggested_work_order.required_parts.length).toBeGreaterThan(0);

      // Verify citations
      const coolantCitation = recommendation.evidence_citations.find(
        (c) => c.parameter === 'engine_coolant_temp_c'
      );
      expect(coolantCitation).toBeDefined();
      expect(coolantCitation?.observed_value).toBe(108.5);
      expect(coolantCitation?.threshold_value).toBe(102);
      expect(coolantCitation?.unit).toBe('°C');
    });
  });

  describe('QA-E04-02: Stale Telemetry Degradation', () => {
    it('degrades confidence and alerts operator when sensor data is stale', () => {
      const assets = loadSeedAssets();
      const staleAsset = assets.find((a) => a.id === 'ast_745_002')!;
      const faults = loadSeedFaults().filter((f) => f.asset_id === staleAsset.id);
      const telemetry = loadSeedTelemetry().filter((t) => t.asset_id === staleAsset.id);

      const latestTelemetry: Record<string, any> = {};
      for (const t of telemetry) {
        latestTelemetry[t.parameter] = t;
      }

      const recommendation = engine.evaluate(staleAsset, faults, latestTelemetry);

      expect(recommendation.confidence_score).toBeLessThan(0.5);
      expect(recommendation.title).toContain('Insufficient Sensor Evidence');
      expect(recommendation.diagnostic_summary).toContain('intermittent or delayed');
      expect(recommendation.urgency).toBe('OBSERVE');
    });
  });

  describe('QA-E04-03: Nominal Operating Asset Evaluation', () => {
    it('evaluates healthy asset with high-confidence nominal recommendation', () => {
      const assets = loadSeedAssets();
      const nominalAsset = assets.find((a) => a.id === 'ast_980_003')!;
      const telemetry = loadSeedTelemetry().filter((t) => t.asset_id === nominalAsset.id);

      const latestTelemetry: Record<string, any> = {};
      for (const t of telemetry) {
        latestTelemetry[t.parameter] = t;
      }

      const recommendation = engine.evaluate(nominalAsset, [], latestTelemetry);

      expect(recommendation.urgency).toBe('OBSERVE');
      expect(recommendation.confidence_score).toBe(0.98);
      expect(recommendation.title).toContain('Nominal Operations');
      expect(recommendation.suggested_work_order.priority).toBe('LOW');
    });
  });

  describe('QA-E04-04: Evidence Citation Traceability', () => {
    it('ensures every citation includes parameter, value, threshold, unit, and timestamp', () => {
      const assets = loadSeedAssets();
      const heroAsset = assets.find((a) => a.id === 'ast_336_001')!;
      const faults = loadSeedFaults().filter((f) => f.asset_id === heroAsset.id);
      const telemetry = loadSeedTelemetry().filter((t) => t.asset_id === heroAsset.id);

      const latestTelemetry: Record<string, any> = {};
      for (const t of telemetry) {
        latestTelemetry[t.parameter] = t;
      }

      const recommendation = engine.evaluate(heroAsset, faults, latestTelemetry);

      for (const citation of recommendation.evidence_citations) {
        expect(citation.parameter).toBeDefined();
        expect(typeof citation.observed_value).toBe('number');
        expect(typeof citation.threshold_value).toBe('number');
        expect(citation.unit).toBeDefined();
        expect(citation.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
      }
    });
  });
});
