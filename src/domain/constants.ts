/**
 * Canonical Units, Parameter Definitions, and Operating Thresholds
 */

export const UNITS = {
  TEMPERATURE: '°C',
  PRESSURE: 'kPa',
  FUEL_RATE: 'L/h',
  ENGINE_SPEED: 'rpm',
  OPERATING_HOURS: 'h',
  PERCENTAGE: '%',
} as const;

export const TELEMETRY_PARAMETERS = {
  COOLANT_TEMP: 'engine_coolant_temp_c',
  OIL_PRESSURE: 'engine_oil_pressure_kpa',
  FUEL_RATE: 'fuel_rate_lph',
  ENGINE_SPEED: 'engine_speed_rpm',
  BATTERY_VOLTAGE: 'battery_voltage_v',
} as const;

export interface ParameterThreshold {
  parameter: string;
  unit: string;
  nominal_min: number;
  nominal_max: number;
  warning_max: number;
  critical_max: number;
}

export const OPERATIONAL_THRESHOLDS: Record<string, ParameterThreshold> = {
  engine_coolant_temp_c: {
    parameter: 'engine_coolant_temp_c',
    unit: '°C',
    nominal_min: 75,
    nominal_max: 98,
    warning_max: 102,
    critical_max: 106,
  },
  engine_oil_pressure_kpa: {
    parameter: 'engine_oil_pressure_kpa',
    unit: 'kPa',
    nominal_min: 250,
    nominal_max: 450,
    warning_max: 220, // Low pressure warning
    critical_max: 180, // Low pressure critical
  },
};

export const DEMO_PERSONA = {
  name: 'Alex Vance',
  role: 'Field Service Supervisor',
  site: 'North Quarry Operations',
};

export const SEED_VERSION = 'seed_cat_2026_v1';
