// Task time estimation (technical spec §8.6.1–§8.6.6; product F4).
import { clamp, median } from '../util';
import type { MachineProfile, Site, TaskAssignment } from '../types';

// ------------------------------------------------------------------------------------------------ baseline §8.6.1

export function ratePerHour(profile: MachineProfile, taskType: string, material: string): number | null {
  const tt = profile.task_types.find((t) => t.task_type === taskType);
  if (!tt) return null;
  const rc = profile.rate_constants;
  switch (tt.rate_model) {
    case 'linear':
    case 'area':
    case 'count':
      return tt.rate_per_hour?.[material] ?? tt.rate_per_hour?.any ?? null;
    case 'bucket': {
      const fill = rc.fill_factor?.[material];
      const cycles = tt.cycles_per_hour_override ?? rc.cycles_per_hour;
      return rc.bucket_capacity_m3 && fill && cycles ? rc.bucket_capacity_m3 * fill * cycles : null;
    }
    case 'haul':
      return rc.payload_t && rc.cycle_min_default ? (rc.payload_t * 60) / rc.cycle_min_default : null;
  }
}

/** baseline_min = quantity / (rate_per_hour × job_efficiency) × 60, job efficiency = site override ?? profile. */
export function baselineMinutes(profile: MachineProfile, site: Site, taskType: string, material: string, quantity: number): number | null {
  const rate = ratePerHour(profile, taskType, material);
  if (rate === null || quantity <= 0) return null;
  const eff = site.job_efficiency_override ?? profile.job_efficiency;
  return (quantity / (rate * eff)) * 60;
}

// ------------------------------------------------------------------------------------------------ artifact §5.4.4

export interface EstimatorArtifact {
  artifact_id: string;
  machine_class: string;
  categorical: { name: string; group: string; levels: string[]; reference: string }[];
  numeric: { name: string; group: string; source: string; transform: 'log1p' | 'ln' | 'identity'; clip: [number, number]; mean: number; std: number }[];
  coefficients: Record<string, number>;
  intercept: number;
  residual_quantiles: {
    pooled: { n: number; q_lo: number; q_mid: number; q_hi: number };
    by_task_type: Record<string, { n: number; q_lo: number; q_mid: number; q_hi: number }>;
  };
  task_type_counts: Record<string, number>;
  min_task_type_count: number;
  min_calibration_n: number;
  fallback_band: { lo: number; hi: number };
}

export interface EstimateFeatures {
  skill_level: string;
  experience_months: number;
  machine_age_years: number;
  task_type: string;
  material: string;
  weather: string;
  visibility: string;
  temperature_band: string;
  time_of_day: string;
  site_congestion: string;
}

export type Basis = 'comparable_history' | 'fallback' | 'insufficient_data';

export interface TaskEstimate {
  basis: Basis;
  baseline_min: number | null;
  p10_min: number | null;
  p50_min: number | null;
  p90_min: number | null;
  factors: { factor: string; pct: number }[];
  artifact_id: string;
  notes: string[];
}

const FACTOR_LABEL: Record<string, (f: EstimateFeatures) => string> = {
  skill: (f) => `Skill level (${f.skill_level})`,
  experience: (f) => `Experience (${f.experience_months} months)`,
  machine_age: (f) => `Machine age (${f.machine_age_years} yrs)`,
  material: (f) => `Material (${f.material})`,
  weather: (f) => ({ rain: 'Rain', windy: 'Wind', dusty: 'Dust', foggy: 'Fog', clear: 'Weather' } as Record<string, string>)[f.weather] ?? 'Weather',
  visibility: (f) => `Visibility (${f.visibility})`,
  temperature: (f) => `Temperature (${f.temperature_band})`,
  time_of_day: (f) => `Time of day (${f.time_of_day})`,
  congestion: (f) => `Site congestion (${f.site_congestion})`,
};

const DEFAULT_BAND = { lo: 0.8, hi: 1.35 };

/** §8.6.2 encoding + §8.6.3 contributions + §8.6.4 basis and range. */
export function estimateTask(baseline: number | null, features: EstimateFeatures, artifact: EstimatorArtifact | null): TaskEstimate {
  if (baseline === null) {
    return { basis: 'insufficient_data', baseline_min: null, p10_min: null, p50_min: null, p90_min: null, factors: [],
      artifact_id: artifact?.artifact_id ?? 'none', notes: ['no rate for this task type and material'] };
  }
  const band = artifact?.fallback_band ?? DEFAULT_BAND;
  const tt = features.task_type;
  const known = artifact && artifact.categorical.find((c) => c.name === 'task_type')?.levels.includes(tt);
  if (!artifact || !known || (artifact.task_type_counts[tt] ?? 0) < artifact.min_task_type_count) {
    return { basis: 'fallback', baseline_min: baseline, p10_min: baseline * band.lo, p50_min: baseline, p90_min: baseline * band.hi,
      factors: [], artifact_id: artifact?.artifact_id ?? 'baseline-fallback@1', notes: [] };
  }
  const notes: string[] = [];
  const values: Record<string, string | number> = { ...features } as unknown as Record<string, string | number>;
  let pred = artifact.intercept;
  const groups: Record<string, number> = {};
  for (const c of artifact.categorical) {
    const v = String(values[c.name]);
    if (!c.levels.includes(v)) notes.push(`unknown_level:${c.name}`);
    if (v === c.reference) continue;
    const coef = artifact.coefficients[`${c.name}=${v}`] ?? 0;
    pred += coef;
    groups[c.group] = (groups[c.group] ?? 0) + coef;
  }
  for (const n of artifact.numeric) {
    const raw = Number(values[n.source === 'experience_months' ? 'experience_months' : n.source === 'machine_age_years' ? 'machine_age_years' : n.source]);
    let v = clamp(raw, n.clip[0], n.clip[1]);
    v = n.transform === 'log1p' ? Math.log1p(v) : n.transform === 'ln' ? Math.log(v) : v;
    const z = (v - n.mean) / n.std;
    const c = (artifact.coefficients[n.name] ?? 0) * z;
    pred += c;
    groups[n.group] = (groups[n.group] ?? 0) + c;
  }
  const byTt = artifact.residual_quantiles.by_task_type[tt];
  const q = byTt && byTt.n >= artifact.min_calibration_n ? byTt : artifact.residual_quantiles.pooled;
  const p = [baseline * Math.exp(pred + q.q_lo), baseline * Math.exp(pred + q.q_mid), baseline * Math.exp(pred + q.q_hi)].sort((a, b) => a - b);
  const factors = Object.entries(groups)
    .filter(([g]) => g !== 'task_type')
    .map(([g, c]) => ({ factor: (FACTOR_LABEL[g] ?? (() => g))(features), pct: Math.round((Math.exp(c) - 1) * 100) }))
    .filter((f) => Math.abs(f.pct) >= 3)
    .sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct) || a.factor.localeCompare(b.factor))
    .slice(0, 3);
  return { basis: 'comparable_history', baseline_min: baseline, p10_min: p[0] ?? null, p50_min: p[1] ?? null, p90_min: p[2] ?? null,
    factors, artifact_id: artifact.artifact_id, notes };
}

// ------------------------------------------------------------------------------------------------ waiting §8.6.5

export function expectedWaitMin(profile: MachineProfile, taskType: string, recentWaits: number[]): number {
  const tt = profile.task_types.find((t) => t.task_type === taskType);
  if (recentWaits.length >= 3) return Math.round(median(recentWaits.slice(-10)) ?? 0);
  return tt?.default_expected_wait_min ?? 0;
}

// ------------------------------------------------------------------------------------------------ live update §8.6.6

export interface LiveInput {
  now: number;
  prior: { p10: number; p50: number; p90: number };
  quantity: number;
  progress: number;
  activeElapsedMin: number;
  paused: boolean;
  expectedWaitMin: number;
  waitingSoFarMin: number;
  siteDelayInProgress: { expectedTotalMin: number; elapsedMin: number } | null;
}

export interface LiveResult {
  mode: 'normal' | 'conditional';
  rem10: number;
  rem50: number;
  rem90: number;
  waitRemaining: number;
  finish10: number;
  finish50: number;
  finish90: number;
  progressPct: number;
}

export function liveUpdate(i: LiveInput): LiveResult {
  const Q = i.quantity;
  const q = clamp(i.progress, 0, Q);
  const p = Q > 0 ? q / Q : 0;
  const a = i.activeElapsedMin;
  let rem10: number;
  let rem50: number;
  let rem90: number;
  if (p === 0 || a < 1) {
    rem10 = Math.max(i.prior.p10 - a, 0.1 * i.prior.p10);
    rem50 = Math.max(i.prior.p50 - a, 0.1 * i.prior.p50);
    rem90 = Math.max(i.prior.p90 - a, 0.1 * i.prior.p90);
  } else {
    const rObs = q / a;
    const rPrior = Q / i.prior.p50;
    const w = Math.min(1, p / 0.3);
    const r = w * rObs + (1 - w) * rPrior;
    rem50 = (Q - q) / r;
    rem10 = rem50 * (1 - (1 - i.prior.p10 / i.prior.p50) * (1 - p));
    rem90 = rem50 * (1 + (i.prior.p90 / i.prior.p50 - 1) * (1 - p));
  }
  const waitRemaining = i.siteDelayInProgress
    ? Math.max(i.siteDelayInProgress.expectedTotalMin - i.siteDelayInProgress.elapsedMin, 1)
    : Math.max(i.expectedWaitMin - i.waitingSoFarMin, 0);
  const minute = 60_000;
  return {
    mode: i.paused ? 'conditional' : 'normal',
    rem10, rem50, rem90, waitRemaining,
    finish10: i.now + (rem10 + waitRemaining) * minute,
    finish50: i.now + (rem50 + waitRemaining) * minute,
    finish90: i.now + (rem90 + waitRemaining) * minute,
    progressPct: Math.round(p * 100),
  };
}

export function taskFeatures(
  task: TaskAssignment,
  operator: { skill_level: string; experience_months: number },
  machine: { year_of_manufacture: number },
  ctx: { weather: string; visibility: string; temperature_band: string; time_of_day: string; site_congestion: string; year: number },
): EstimateFeatures {
  return {
    skill_level: operator.skill_level,
    experience_months: operator.experience_months,
    machine_age_years: Math.max(0, ctx.year - machine.year_of_manufacture),
    task_type: task.task_type,
    material: task.material,
    weather: ctx.weather,
    visibility: ctx.visibility,
    temperature_band: ctx.temperature_band,
    time_of_day: ctx.time_of_day,
    site_congestion: ctx.site_congestion,
  };
}
