// Effective working conditions (technical spec §8.4): operator reports within 2 h override the forecast.
import { isDark, HOUR } from '../util';
import type { ForecastHour, MachineProfile, Site } from '../types';

export type ConditionName = 'rain' | 'dust' | 'darkness' | 'heat' | 'wind';

export interface ConditionReport {
  condition: ConditionName;
  active: boolean;
  at: number;
}

export interface EffectiveConditions {
  rain: boolean;
  dust: boolean;
  darkness: boolean;
  heat_index_c: number | null;
  wind_kmh: number | null;
  visibility_m: number | null;
  temp_c: number | null;
  multiplier: number;
  forecast_age_ms: number | null;
  sources: Record<'rain' | 'dust' | 'darkness', 'report' | 'forecast' | 'clock' | 'simulator' | 'none'>;
}

export function forecastAt(hours: ForecastHour[], ts: number): ForecastHour | null {
  return hours.find((h) => h.valid_from <= ts && ts < h.valid_to) ?? null;
}

export function effectiveConditions(
  now: number,
  site: Site,
  profile: MachineProfile,
  forecast: ForecastHour[],
  reports: ConditionReport[],
): EffectiveConditions {
  const latest = (c: ConditionName) =>
    [...reports].reverse().find((r) => r.condition === c && now - r.at <= 2 * HOUR) ?? null;
  const hour = forecastAt(forecast, now);
  const rainReport = latest('rain');
  const dustReport = latest('dust');
  const darkReport = latest('darkness');
  const rain = rainReport ? rainReport.active : !!hour && (hour.weather === 'rain' || hour.precipitation_mm >= 0.5);
  const dust = dustReport ? dustReport.active : !!hour && hour.weather === 'dusty';
  const darkness = darkReport ? darkReport.active : isDark(now, site);
  const m = profile.condition_modifiers;
  const multiplier = Math.min(m.cap, (rain ? m.rain : 1) * (dust ? m.dust : 1) * (darkness ? m.darkness : 1));
  const sim = (r: ConditionReport | null) => (r ? 'report' : 'forecast');
  return {
    rain,
    dust,
    darkness,
    heat_index_c: hour?.heat_index_c ?? null,
    wind_kmh: hour?.wind_kmh ?? null,
    visibility_m: hour?.visibility_m ?? null,
    temp_c: hour?.temp_c ?? null,
    multiplier: Math.round(multiplier * 1000) / 1000,
    forecast_age_ms: hour ? now - hour.issued_at : null,
    sources: {
      rain: rainReport ? 'report' : hour ? sim(null) : 'none',
      dust: dustReport ? 'report' : hour ? sim(null) : 'none',
      darkness: darkReport ? 'report' : 'clock',
    },
  };
}
