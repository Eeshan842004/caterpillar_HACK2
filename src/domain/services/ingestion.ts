import { TelemetryPoint, DataQualityState } from '../types';

export interface RawTelemetryInput {
  asset_id: string;
  parameter: string;
  value: number;
  unit: string;
  observed_at: string;
  raw_payload?: string;
}

export class IngestionService {
  /**
   * Validates and normalizes raw telemetry into a canonical TelemetryPoint.
   */
  public process(input: RawTelemetryInput): TelemetryPoint {
    const ingested_at = new Date().toISOString();
    const quality = this.determineQuality(input.parameter, input.value, input.observed_at);

    return {
      id: `tel_${Math.random().toString(36).substring(2, 9)}`,
      asset_id: input.asset_id,
      parameter: input.parameter,
      value: input.value,
      unit: input.unit,
      observed_at: input.observed_at,
      ingested_at,
      quality,
      raw_input: input.raw_payload || JSON.stringify(input),
    };
  }

  /**
   * Assesses sensor data quality against physical boundaries and freshness limits.
   */
  public determineQuality(parameter: string, value: number, observedAt: string): DataQualityState {
    const observedTime = new Date(observedAt).getTime();
    const now = Date.now();

    // Check for stale readings (> 2 hours old)
    const TWO_HOURS_MS = 2 * 60 * 60 * 1000;
    if (now - observedTime > TWO_HOURS_MS) {
      return 'STALE';
    }

    // Physical plausibility checks
    if (parameter === 'engine_coolant_temp_c') {
      if (value < -40 || value > 150) {
        return 'OUT_OF_RANGE';
      }
    } else if (parameter === 'engine_oil_pressure_kpa') {
      if (value < 0 || value > 1200) {
        return 'OUT_OF_RANGE';
      }
    } else if (parameter === 'fuel_rate_lph') {
      if (value < 0 || value > 300) {
        return 'OUT_OF_RANGE';
      }
    }

    return 'GOOD';
  }
}
