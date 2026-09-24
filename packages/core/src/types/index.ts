// Domain types and enums — technical spec §5.1, §5.3, §5.4.1. JSON keys are snake_case (§4.2).

export const MACHINE_STATES = ['OFF', 'SECURED', 'READY', 'WORKING', 'TRAVELLING', 'UNKNOWN'] as const;
export type MachineState = (typeof MACHINE_STATES)[number];

export type TaskState = 'PLANNED' | 'ACTIVE' | 'PAUSED' | 'BLOCKED' | 'COMPLETED' | 'CANCELLED';
export type AlertLevel = 'INFO' | 'CAUTION' | 'WARNING' | 'CRITICAL' | 'ADVISORY';
export type AlertType =
  | 'A-BELT-MOVE' | 'A-BELT-OPER' | 'A-BELT-UNAV'
  | 'A-PROX-CAUT' | 'A-PROX-WARN' | 'A-PROX-CRIT' | 'A-PROX-UNAV'
  | 'A-SPEED' | 'A-HEAT' | 'A-WIND' | 'A-IDLE-ASK' | 'A-EXIT-UNSEC' | 'A-SOS';
export type AlertStatus = 'RAISED' | 'ACKNOWLEDGED' | 'CLEARED' | 'REVIEWED';
export type Source = 'observed' | 'reported' | 'inferred' | 'reviewed';
export type Audience = 'operator_only' | 'next_operator' | 'site' | 'trainer' | 'safety';
export type SyncStatus = 'local_only' | 'pending' | 'sent' | 'confirmed' | 'needs_review' | 'rejected';
export type LedgerKind =
  | 'observation' | 'report' | 'inference' | 'alert' | 'incident' | 'task_event' | 'idle_event'
  | 'handover_item' | 'learning_event' | 'correction' | 'shift_event';
export type IdleReason =
  | 'waiting_truck' | 'waiting_loader' | 'shovel_queue' | 'crusher_queue' | 'access_blocked'
  | 'instructed_hold' | 'break' | 'other';
export type IdleCategory = 'site_delay' | 'break' | 'other';
export type IdleClass = 'required' | 'reported' | 'unexplained';
export type BlockReason = 'access_blocked' | 'utility_mark' | 'waiting_instruction' | 'machine_fault' | 'weather' | 'other';
export type ReassignReason = 'machine_fault' | 'not_trained' | 'access_blocked' | 'wrong_machine' | 'other';
export type ObjectType = 'person' | 'light_vehicle' | 'heavy_vehicle' | 'structure' | 'unknown';
export type Place =
  | 'front' | 'front_right' | 'right' | 'rear_right' | 'rear' | 'rear_left' | 'left' | 'front_left' | 'unknown';
export type Weather = 'clear' | 'rain' | 'windy' | 'dusty' | 'foggy';
export type VisibilityBand = 'good' | 'moderate' | 'poor';
export type ImpactRisk = 'none' | 'at_risk' | 'likely_miss' | 'unavailable';
export type Language = 'en' | 'hi' | 'ta';
export type Unit = 'm' | 'm2' | 'm3' | 't' | 'loads' | 'lifts';

export const SITE_DELAY_REASONS: ReadonlySet<IdleReason> = new Set([
  'waiting_truck', 'waiting_loader', 'shovel_queue', 'crusher_queue', 'access_blocked', 'instructed_hold',
]);

export function idleCategory(reason: IdleReason): IdleCategory {
  if (SITE_DELAY_REASONS.has(reason)) return 'site_delay';
  return reason === 'break' ? 'break' : 'other';
}

// ------------------------------------------------------------------------------------------------ signals

export type SignalName =
  | 'engine_on' | 'ground_speed_kmh' | 'hydraulic_lockout' | 'park_brake' | 'seatbelt_fastened' | 'seat_occupied'
  | 'cab_door_open' | 'implement_neutral' | 'load_factor_pct' | 'implement_active' | 'swing_active'
  | 'travel_direction' | 'load_cycles' | 'progress_units' | 'coolant_temp_c' | 'fuel_used_l' | 'engine_hours'
  | 'regen_active' | 'lat' | 'lon' | 'heading_deg';

export type SignalValue = number | boolean | string;

export interface SignalSample {
  ts: number;
  values: Partial<Record<SignalName, SignalValue>>;
}

export interface DetectionEvent {
  ts: number;
  object_id: string;
  type: ObjectType;
  bearing_deg: number;
  distance_m: number;
  closing_mps: number;
  quality: number;
}

export interface ProximityHeartbeat {
  ts: number;
  quality: number;
}

// ------------------------------------------------------------------------------------------------ profile

export interface TaskTypeProfile {
  task_type: string;
  unit: Unit;
  rate_model: 'linear' | 'area' | 'count' | 'bucket' | 'haul';
  rate_per_hour?: Record<string, number>;
  cycles_per_hour_override?: number;
  default_expected_wait_min: number;
  wind_sensitive: boolean;
  guided_card_id?: string;
  content_tags?: string[];
}

export interface RadialProximity {
  mode: 'radial';
  inner_m: number;
  outer_m: number;
}

export interface PathProximity {
  mode: 'path';
  reverse: { sector_deg: [number, number]; inner_m: number; outer_m: number };
  forward: { sector_deg: [number, number]; inner_m: number; outer_m: number };
  stationary_inner_m: number;
}

export type ProximityProfile = (RadialProximity | PathProximity) & {
  ttc_caution_s: number;
  ttc_warning_s: number;
  departing_mps: number;
  closing_min_mps: number;
  heartbeat_stale_ms: number;
  min_quality: number;
  clear_after_s: number;
  group_window_s: number;
  provenance?: string;
};

export interface MachineProfile {
  profile_id: string;
  version: number;
  machine_class: 'excavator' | 'haul_truck' | 'wheel_loader';
  display_name: string;
  sector: 'construction' | 'mining';
  illustrative_notice: string;
  signals: Partial<Record<SignalName, { freshness_ms: number }>>;
  secure_signal: 'hydraulic_lockout' | 'park_brake';
  state_thresholds: {
    travel_speed_kmh: number;
    stationary_speed_kmh: number;
    working_load_factor_pct: number;
    load_cycle_window_s: number;
    debounce_s: number;
  };
  job_efficiency: number;
  rate_constants: {
    bucket_capacity_m3?: number;
    cycles_per_hour?: number;
    fill_factor?: Record<string, number>;
    payload_t?: number;
    cycle_min_default?: number;
  };
  task_types: TaskTypeProfile[];
  idle: {
    threshold_s: number;
    cooldown_required_s: number;
    cooldown_trigger_load_pct: number;
    cooldown_lookback_s: number;
    warmup_max_s: number;
    warmup_coolant_c: number;
    fuel_idle_lph: number;
    engine_off_suggest_min: number;
    prompt_timeout_s: number;
    reasons: IdleReason[];
    default_reason_order: IdleReason[];
    default_expected_wait_min: Partial<Record<IdleReason, number>>;
  };
  seatbelt: {
    debounce_s: number;
    critical_repeat_s: number;
    warning_repeat_s: number;
    move_snapshot_after_s: number;
    flap_changes: number;
    flap_window_s: number;
    repeat_finding_count: number;
  };
  safe_exit: { exit_intent_window_s: number; motion_stop_kmh: number; requires: SignalName[] };
  proximity: ProximityProfile;
  condition_modifiers: { rain: number; dust: number; darkness: number; cap: number; provenance?: string };
  heat?: { heat_index_c: number; continuous_work_min: number; repeat_min: number };
  wind?: { threshold_kmh: number };
  speed: { default_limit_kmh: number; overspeed_hold_s: number; repeat_s: number } | null;
  content_pack: string | null;
  training?: {
    condition_prep: Partial<Record<'rain' | 'dust' | 'darkness', string[]>>;
    prep_exposure_threshold: number;
    prep_max_experience_months: number;
    prep_lookahead_h: number;
  };
}

// ------------------------------------------------------------------------------------------------ reference data

export interface Site {
  site_id: string;
  name: string;
  sector: 'construction' | 'mining';
  lat: number;
  lon: number;
  utc_offset_minutes: number;
  diesel_price_inr_per_l: number;
  dark_start_local: string;
  dark_end_local: string;
  job_efficiency_override: number | null;
  congestion_level: 'low' | 'medium' | 'high';
}

export interface Zone {
  zone_id: string;
  site_id: string;
  name: string;
  kind: string;
  center_lat: number;
  center_lon: number;
  radius_m: number;
  speed_limit_kmh: number | null;
}

export interface MachineRef {
  machine_id: string;
  short_id: number;
  site_id: string;
  profile_id: string;
  profile_version: number;
  machine_class: string;
  model_name: string;
  year_of_manufacture: number;
  detail_level: 'detailed' | 'status_only';
}

export interface OperatorRef {
  operator_id: string;
  display_name: string;
  language: Language;
  skill_level: 'beginner' | 'intermediate' | 'expert';
  experience_months: number;
  hired_at: string;
  site_id: string;
  pin_salt: string;
  pin_hash: string;
  pin_iterations: number;
}

export interface TaskAssignment {
  task_id: string;
  site_id: string;
  machine_id: string | null;
  task_type: string;
  zone_id: string | null;
  location_text: string;
  quantity: number;
  unit: Unit;
  material: string;
  priority: number;
  completion_criterion: string;
  planner_minutes: number | null;
  planned_date: string;
  planned_start_at: number | null; // epoch ms
  planned_start_window_min: number;
  sequence: number;
  source: 'dispatcher' | 'seed' | 'reassignment';
  revision: number;
  status: 'assigned' | 'cancelled';
}

export interface ForecastHour {
  valid_from: number;
  valid_to: number;
  weather: Weather;
  visibility: VisibilityBand;
  visibility_m: number | null;
  temp_c: number;
  heat_index_c: number | null;
  wind_kmh: number;
  precipitation_mm: number;
  issued_at: number;
  source: 'seed' | 'open_meteo' | 'sim_weather';
}

export interface HandoverItemRef {
  item_id: string;
  item_type: 'unfinished_task' | 'blocked_task' | 'defect' | 'incident' | 'site_delay' | 'note' | 'tip';
  text: string;
  audiences: Audience[];
  status: 'open' | 'resolved' | 'removed';
  task_id: string | null;
  incident_id: string | null;
  from_operator_id: string | null;
  created_at: number;
}

// ------------------------------------------------------------------------------------------------ ledger

export interface LedgerEntry {
  entry_id: string;
  device_id: string;
  shift_id: string | null;
  machine_id: string;
  operator_id: string | null;
  kind: LedgerKind;
  subtype: string;
  source: Source;
  payload: Record<string, unknown>;
  observed_at: number;
  recorded_at: number;
  freshness_s: number | null;
  confidence: 'high' | 'medium' | 'low' | null;
  rule_or_model_version: string | null;
  original_text: string | null;
  supersedes: string | null;
  audience: Audience;
  data_origin: string;
  sync_status: SyncStatus;
  chain_seq: number | null;
  prev_hash: string | null;
  content_hash: string | null;
  canonical_payload: string | null;
}
