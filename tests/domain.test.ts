import { describe, it, expect } from 'vitest';
import {
  loadSeedAssets,
  loadSeedFaults,
  loadSeedTelemetry,
  HERO_GROUND_TRUTH,
} from '@/domain/fixtures/loader';
import { OPERATIONAL_THRESHOLDS, UNITS } from '@/domain/constants';

describe('Epic E-02: Domain Contracts & Deterministic Fixtures', () => {
  describe('QA-E02-01: Identifier Separation Invariant', () => {
    it('ensures internal asset IDs are distinct from external serial numbers', () => {
      const assets = loadSeedAssets();
      expect(assets.length).toBeGreaterThanOrEqual(4);

      for (const asset of assets) {
        expect(asset.id).toMatch(/^ast_[0-9a-zA-Z_]+$/);
        expect(asset.serial_number).toMatch(/^CAT-[0-9]{3}-[A-Z]{3}-[0-9]{4}$/);
        expect(asset.id).not.toBe(asset.serial_number);
        expect(asset.is_synthetic).toBe(true);
      }
    });
  });

  describe('QA-E02-02: Dual Timestamp & UTC Invariant', () => {
    it('verifies observed_at and ingested_at are valid UTC ISO 8601 strings', () => {
      const telemetry = loadSeedTelemetry();
      expect(telemetry.length).toBeGreaterThanOrEqual(8);

      for (const point of telemetry) {
        const obsDate = new Date(point.observed_at);
        const ingDate = new Date(point.ingested_at);

        expect(isNaN(obsDate.getTime())).toBe(false);
        expect(isNaN(ingDate.getTime())).toBe(false);
        expect(point.observed_at.endsWith('Z')).toBe(true);
        expect(point.ingested_at.endsWith('Z')).toBe(true);
        expect(ingDate.getTime()).toBeGreaterThanOrEqual(obsDate.getTime());
      }
    });
  });

  describe('QA-E02-03: Data Quality Enum Integrity', () => {
    it('restricts telemetry data quality to approved enum states', () => {
      const validQualities = ['GOOD', 'SUSPECT', 'STALE', 'MISSING', 'OUT_OF_RANGE'];
      const telemetry = loadSeedTelemetry();

      for (const point of telemetry) {
        expect(validQualities).toContain(point.quality);
      }

      const stalePoint = telemetry.find((p) => p.quality === 'STALE');
      expect(stalePoint).toBeDefined();
      expect(stalePoint?.asset_id).toBe('ast_745_002');
    });
  });

  describe('QA-E02-04: Ground Truth Anomaly Verification', () => {
    it('confirms hero asset ast_336_001 exhibits escalating coolant overheating', () => {
      const heroId = HERO_GROUND_TRUTH.heroAssetId;
      const telemetry = loadSeedTelemetry().filter(
        (p) => p.asset_id === heroId && p.parameter === HERO_GROUND_TRUTH.expectedCriticalParam
      );

      expect(telemetry.length).toBeGreaterThanOrEqual(4);

      // Verify escalating temperature trajectory
      const values = telemetry.map((t) => t.value);
      expect(values[0]).toBeLessThan(100);
      const peakValue = Math.max(...values);
      expect(peakValue).toBe(108.5);
      expect(peakValue).toBeGreaterThan(HERO_GROUND_TRUTH.criticalThreshold);

      // Verify active critical diagnostic fault
      const faults = loadSeedFaults().filter((f) => f.asset_id === heroId);
      const criticalFault = faults.find((f) => f.spn === 110 && f.fmi === 0);
      expect(criticalFault).toBeDefined();
      expect(criticalFault?.severity).toBe('CRITICAL');
      expect(criticalFault?.is_active).toBe(true);
    });
  });

  describe('QA-E02-05: Immutability and Reset Determinism', () => {
    it('ensures deep-cloned fixture loader prevents mutation leakage', () => {
      const originalAssets = loadSeedAssets();
      const firstAsset = originalAssets[0];

      // Mutate in-memory copy
      firstAsset.engine_hours = 999999;
      firstAsset.status = 'OFFLINE';

      // Reload fresh copy
      const freshAssets = loadSeedAssets();
      expect(freshAssets[0].engine_hours).toBe(3412.5);
      expect(freshAssets[0].status).toBe('CRITICAL');
    });
  });

  describe('Operational Thresholds & Units', () => {
    it('validates canonical threshold definitions', () => {
      const coolantThreshold = OPERATIONAL_THRESHOLDS.engine_coolant_temp_c;
      expect(coolantThreshold.unit).toBe(UNITS.TEMPERATURE);
      expect(coolantThreshold.warning_max).toBe(102);
      expect(coolantThreshold.critical_max).toBe(106);
    });
  });
});
