// First-launch import of the demo seed and demo history (technical spec §5.4.2, T16 seed mapping).
// Day offsets map to the SITE-LOCAL date of `now`; "HH:MM" planned starts are site-local times.
import type {
  ForecastHour, HandoverItemRef, LedgerEntry, MachineRef, OperatorRef, Site, TaskAssignment, Unit, Weather, VisibilityBand, Zone,
} from '../types';
import { HOUR, MINUTE } from '../util';

/* eslint-disable @typescript-eslint/no-explicit-any */
export interface DemoSeed {
  sites: any[];
  zones: any[];
  machines: any[];
  operators: any[];
  assignments: any[];
  handovers: any[];
  forecast: any[];
}

export interface DeviceData {
  site: Site;
  zones: Zone[];
  machine: MachineRef;
  operators: OperatorRef[];
  assignments: TaskAssignment[];
  forecast: ForecastHour[];
  handoverItems: HandoverItemRef[];
  history: LedgerEntry[];
}

function siteMidnightUtc(now: number, offsetMin: number): number {
  const local = now + offsetMin * MINUTE;
  return Math.floor(local / (24 * HOUR)) * 24 * HOUR - offsetMin * MINUTE;
}

export function deviceDataFromSeed(seed: DemoSeed, history: any[], machineId: string, now: number): DeviceData {
  const m = seed.machines.find((x) => x.machine_id === machineId);
  if (!m) throw new Error(`Machine ${machineId} is not in the demo seed`);
  const s = seed.sites.find((x) => x.site_id === m.site_id);
  if (!s) throw new Error(`Site ${m.site_id} is not in the demo seed`);
  const site: Site = {
    site_id: s.site_id, name: s.name, sector: s.sector, lat: s.lat, lon: s.lon, utc_offset_minutes: s.utc_offset_minutes,
    diesel_price_inr_per_l: s.diesel_price_inr_per_l, dark_start_local: s.dark_start_local, dark_end_local: s.dark_end_local,
    job_efficiency_override: s.job_efficiency_override ?? null, congestion_level: s.congestion_level,
  };
  const midnight = siteMidnightUtc(now, site.utc_offset_minutes);
  const localDate = (dayOffset: number) => new Date(midnight + dayOffset * 24 * HOUR + site.utc_offset_minutes * MINUTE).toISOString().slice(0, 10);

  const assignments: TaskAssignment[] = seed.assignments
    .filter((a) => a.machine_id === machineId)
    .map((a) => {
      const day = a.planned_day_offset ?? 0;
      let start: number | null = null;
      if (a.planned_start_local) {
        const [hh, mm] = String(a.planned_start_local).split(':').map(Number);
        start = midnight + day * 24 * HOUR + ((hh ?? 0) * 60 + (mm ?? 0)) * MINUTE;
      }
      return {
        task_id: a.task_id, site_id: a.site_id, machine_id: a.machine_id, task_type: a.task_type, zone_id: a.zone_id ?? null,
        location_text: a.location_text, quantity: a.quantity, unit: a.unit as Unit, material: a.material, priority: a.priority,
        completion_criterion: a.completion_criterion, planner_minutes: a.planner_minutes ?? null, planned_date: localDate(day),
        planned_start_at: start, planned_start_window_min: a.planned_start_window_min ?? 15, sequence: a.sequence,
        source: a.source ?? 'seed', revision: 1, status: 'assigned',
      };
    });

  const hourStart = Math.floor((now + site.utc_offset_minutes * MINUTE) / HOUR) * HOUR - site.utc_offset_minutes * MINUTE;
  const issued = midnight - 6 * HOUR;       // 18:00 site-local yesterday
  const forecast: ForecastHour[] = seed.forecast
    .filter((f) => f.site_id === site.site_id)
    .map((f) => ({
      valid_from: hourStart + f.hour_offset * HOUR, valid_to: hourStart + (f.hour_offset + 1) * HOUR,
      weather: f.weather as Weather, visibility: f.visibility as VisibilityBand, visibility_m: f.visibility_m ?? null,
      temp_c: f.temp_c, heat_index_c: f.heat_index_c ?? null, wind_kmh: f.wind_kmh, precipitation_mm: f.precipitation_mm,
      issued_at: issued, source: 'seed' as const,
    }))
    .sort((a, b) => a.valid_from - b.valid_from);

  const handoverItems: HandoverItemRef[] = [];
  for (const ho of seed.handovers.filter((h) => h.machine_id === machineId)) {
    for (const item of ho.items) {
      handoverItems.push({
        item_id: item.item_id, item_type: item.item_type, text: item.text, audiences: item.audiences, status: item.status,
        task_id: item.task_id ?? null, incident_id: item.incident_id ?? null, from_operator_id: ho.from_operator_id ?? null,
        created_at: now + (ho.created_offset_min ?? -480) * MINUTE,
      });
    }
  }

  // History: shift each entry so its day offset lands on the same offset from today (dates mapped to today, §4.4 seed.ts)
  const mapped: LedgerEntry[] = history
    .filter((e) => e.machine_id === machineId)
    .map((e) => {
      const obs = Date.parse(e.observed_at);
      const rec = Date.parse(e.recorded_at);
      const shift = midnight + (e.day_offset ?? 0) * 24 * HOUR - siteMidnightUtc(obs, site.utc_offset_minutes);
      return { ...e, observed_at: obs + shift, recorded_at: rec + shift, sync_status: 'confirmed' } as LedgerEntry;
    });

  const opIds = new Set(seed.operators.filter((o) => o.site_id === site.site_id).map((o) => o.operator_id));
  return {
    site,
    zones: seed.zones.filter((z) => z.site_id === site.site_id).map((z) => ({ ...z, speed_limit_kmh: z.speed_limit_kmh ?? null })),
    machine: {
      machine_id: m.machine_id, short_id: m.short_id, site_id: m.site_id, profile_id: m.profile_id,
      profile_version: m.profile_version, machine_class: m.machine_class, model_name: m.model_name,
      year_of_manufacture: m.year_of_manufacture, detail_level: m.detail_level,
    },
    operators: seed.operators.filter((o) => opIds.has(o.operator_id)).map((o) => ({
      operator_id: o.operator_id, display_name: o.display_name, language: o.language, skill_level: o.skill_level,
      experience_months: o.experience_months, hired_at: o.hired_at, site_id: o.site_id, pin_salt: o.pin_salt,
      pin_hash: o.pin_hash, pin_iterations: o.pin_iterations,
    })),
    assignments,
    forecast,
    handoverItems,
    history: mapped,
  };
}
