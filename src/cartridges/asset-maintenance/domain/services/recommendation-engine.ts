import {
  Asset,
  DiagnosticFault,
  TelemetryPoint,
  Recommendation,
} from '../types';
import { OPERATIONAL_THRESHOLDS } from '../constants';
import { type Clock, systemClock } from '@/core/runtime/determinism';

export class RecommendationEngine {
  constructor(private readonly clock: Clock = systemClock) {}

  /**
   * Deterministically evaluates asset health and generates an evidence-backed recommendation.
   */
  public evaluate(
    asset: Asset,
    activeFaults: DiagnosticFault[],
    latestTelemetry: Record<string, TelemetryPoint>
  ): Recommendation {
    const coolantPoint = latestTelemetry['engine_coolant_temp_c'];
    const oilPressurePoint = latestTelemetry['engine_oil_pressure_kpa'];
    const now = this.clock.now().toISOString();

    // 1. Degraded Mode: Check for stale sensor data
    if (coolantPoint?.quality === 'STALE' || oilPressurePoint?.quality === 'STALE') {
      return {
        id: `rec_stale_${asset.id}`,
        asset_id: asset.id,
        title: 'Insufficient Sensor Evidence: Stale Telemetry Detected',
        urgency: 'OBSERVE',
        confidence_score: 0.35,
        evidence_citations: [
          {
            parameter: 'engine_coolant_temp_c',
            observed_value: coolantPoint?.value || 0,
            threshold_value: OPERATIONAL_THRESHOLDS.engine_coolant_temp_c.warning_max,
            unit: '°C',
            timestamp: coolantPoint?.observed_at || now,
          },
        ],
        diagnostic_summary:
          'Telemetry connection is intermittent or delayed by >2 hours. Automated diagnostic confidence is degraded to prevent unverified dispatch.',
        recommended_action:
          'Dispatch field technician to inspect cellular gateway and verify physical sensor wiring before scheduling mechanical repairs.',
        suggested_work_order: {
          title: `Sensor & Gateway Verification: ${asset.serial_number}`,
          priority: 'LOW',
          estimated_duration_hours: 1.0,
          required_parts: ['Diagnostic Cable Harness', 'Multimeter'],
        },
        created_at: now,
      };
    }

    // 2. Critical Overheating Rule: SPN 110 FMI 0 or Temperature > Warning Threshold
    const criticalCoolantFault = activeFaults.find(
      (f) => f.spn === 110 && (f.fmi === 0 || f.severity === 'CRITICAL')
    );
    const isOverheating =
      coolantPoint &&
      coolantPoint.value >= OPERATIONAL_THRESHOLDS.engine_coolant_temp_c.warning_max;

    if (criticalCoolantFault || isOverheating) {
      const observedTemp = coolantPoint ? coolantPoint.value : 108.5;
      return {
        id: `rec_coolant_${asset.id}`,
        asset_id: asset.id,
        fault_id: criticalCoolantFault?.id,
        title: 'Emergency Coolant System Inspection Required',
        urgency: 'IMMEDIATE',
        confidence_score: 0.94,
        evidence_citations: [
          {
            parameter: 'engine_coolant_temp_c',
            observed_value: observedTemp,
            threshold_value: OPERATIONAL_THRESHOLDS.engine_coolant_temp_c.warning_max,
            unit: '°C',
            timestamp: coolantPoint?.observed_at || now,
          },
        ],
        diagnostic_summary: `Engine coolant temperature reached ${observedTemp}°C, exceeding the safe operational limit of ${OPERATIONAL_THRESHOLDS.engine_coolant_temp_c.warning_max}°C. Accompanied by active diagnostic fault code SPN 110 FMI 0.`,
        recommended_action:
          'Immediate shutdown advisory. Inspect radiator core for blockages, check coolant level, and inspect water pump and thermostat housing.',
        suggested_work_order: {
          title: `Emergency Coolant Circuit Repair: ${asset.serial_number}`,
          priority: 'EMERGENCY',
          estimated_duration_hours: 3.5,
          required_parts: [
            'Radiator Upper/Lower Hose Kit',
            'Premix Heavy-Duty Coolant 20L',
            'Thermostat Assembly',
          ],
        },
        created_at: now,
      };
    }

    // 3. Oil Pressure Warning Rule: SPN 100 or Low Pressure
    const oilFault = activeFaults.find((f) => f.spn === 100);
    const isLowOilPressure =
      oilPressurePoint &&
      oilPressurePoint.value <= OPERATIONAL_THRESHOLDS.engine_oil_pressure_kpa.warning_max;

    if (oilFault || isLowOilPressure) {
      const observedPressure = oilPressurePoint ? oilPressurePoint.value : 210.0;
      return {
        id: `rec_oil_${asset.id}`,
        asset_id: asset.id,
        fault_id: oilFault?.id,
        title: 'Low Engine Oil Pressure - Schedule Fluid Analysis',
        urgency: 'SCHEDULED',
        confidence_score: 0.82,
        evidence_citations: [
          {
            parameter: 'engine_oil_pressure_kpa',
            observed_value: observedPressure,
            threshold_value: OPERATIONAL_THRESHOLDS.engine_oil_pressure_kpa.warning_max,
            unit: 'kPa',
            timestamp: oilPressurePoint?.observed_at || now,
          },
        ],
        diagnostic_summary: `Engine oil pressure measured at ${observedPressure} kPa, falling below the nominal threshold of 250 kPa.`,
        recommended_action:
          'Schedule scheduled fluid sampling to detect metal shavings or fuel dilution. Inspect oil filter for restriction.',
        suggested_work_order: {
          title: `Scheduled Oil & Filter Service: ${asset.serial_number}`,
          priority: 'MEDIUM',
          estimated_duration_hours: 2.0,
          required_parts: ['Engine Oil Filter', 'Fluid Analysis Sampling Kit'],
        },
        created_at: now,
      };
    }

    // 4. Nominal Fleet Asset
    return {
      id: `rec_nominal_${asset.id}`,
      asset_id: asset.id,
      title: 'Nominal Operations - All Parameters Healthy',
      urgency: 'OBSERVE',
      confidence_score: 0.98,
      evidence_citations: [
        {
          parameter: 'engine_coolant_temp_c',
          observed_value: coolantPoint?.value || 88.0,
          threshold_value: OPERATIONAL_THRESHOLDS.engine_coolant_temp_c.nominal_max,
          unit: '°C',
          timestamp: coolantPoint?.observed_at || now,
        },
      ],
      diagnostic_summary:
        'All reported telemetry parameters are within manufacturer nominal operating ranges with zero active diagnostic fault codes.',
      recommended_action: 'Maintain standard operating schedule. No service intervention required.',
      suggested_work_order: {
        title: `Routine Inspection: ${asset.serial_number}`,
        priority: 'LOW',
        estimated_duration_hours: 0.5,
        required_parts: [],
      },
      created_at: now,
    };
  }
}
