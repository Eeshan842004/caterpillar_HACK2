import { Asset, DiagnosticFault, TelemetryPoint } from '../types';
import seedAssets from './seed_assets.json';
import seedFaults from './seed_faults.json';
import seedTelemetry from './seed_telemetry.json';

/**
 * Deep clone helper to ensure immutability and reset determinism.
 */
function deepClone<T>(data: T): T {
  return JSON.parse(JSON.stringify(data));
}

export function loadSeedAssets(): Asset[] {
  return deepClone(seedAssets) as Asset[];
}

export function loadSeedFaults(): DiagnosticFault[] {
  return deepClone(seedFaults) as DiagnosticFault[];
}

export function loadSeedTelemetry(): TelemetryPoint[] {
  return deepClone(seedTelemetry) as TelemetryPoint[];
}

export interface GroundTruthScenario {
  heroAssetId: string;
  expectedCriticalParam: string;
  criticalThreshold: number;
  expectedFaultCode: string;
  expectedRecommendationTitle: string;
}

export const HERO_GROUND_TRUTH: GroundTruthScenario = {
  heroAssetId: 'ast_336_001',
  expectedCriticalParam: 'engine_coolant_temp_c',
  criticalThreshold: 102.0,
  expectedFaultCode: 'SPN 110 FMI 0',
  expectedRecommendationTitle: 'Emergency Coolant System Inspection',
};
