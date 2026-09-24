// Pure helpers (no Date.now / Math.random / timers — the app injects clock and ids, §4.2).
import type { Site, Zone } from '../types';

export interface Clock {
  now(): number;
}

export class SimClock implements Clock {
  constructor(private t: number) {}
  now(): number {
    return this.t;
  }
  set(t: number): void {
    this.t = t;
  }
  advance(ms: number): void {
    this.t += ms;
  }
}

export type IdGen = () => string;

/** Deterministic ids for tests (`t-1`, `t-2`, …). */
export function sequentialIds(prefix = 'id'): IdGen {
  let n = 0;
  return () => `${prefix}-${++n}`;
}

export const MINUTE = 60_000;
export const HOUR = 3_600_000;

/** Site-local wall-clock parts (UTC + fixed offset, A-04 / DR-15). */
export function toLocal(ts: number, offsetMin: number): { hour: number; minute: number; date: string } {
  const d = new Date(ts + offsetMin * MINUTE);
  return {
    hour: d.getUTCHours(),
    minute: d.getUTCMinutes(),
    date: d.toISOString().slice(0, 10),
  };
}

export function formatHHMM(ts: number, offsetMin: number): string {
  const { hour, minute } = toLocal(ts, offsetMin);
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
}

export function parseHHMM(text: string): number {
  const [h, m] = text.split(':');
  return Number(h) * 60 + Number(m);
}

/** Darkness from the site's dark window, which usually wraps midnight (19:00–06:00). */
export function isDark(ts: number, site: Site): boolean {
  const { hour, minute } = toLocal(ts, site.utc_offset_minutes);
  const m = hour * 60 + minute;
  const start = parseHHMM(site.dark_start_local);
  const end = parseHHMM(site.dark_end_local);
  return start > end ? m >= start || m < end : m >= start && m < end;
}

export function timeOfDayBand(ts: number, offsetMin: number): 'morning' | 'afternoon' | 'evening' | 'night' {
  const { hour } = toLocal(ts, offsetMin);
  if (hour >= 6 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 18) return 'afternoon';
  if (hour >= 18 && hour < 22) return 'evening';
  return 'night';
}

export function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? (s[mid] as number) : ((s[mid - 1] as number) + (s[mid] as number)) / 2;
}

export function haversineM(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6_371_000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

/** Circle zones; the smallest containing radius wins (§4.3 util/geo). */
export function zoneAt(lat: number, lon: number, zones: Zone[]): Zone | null {
  let best: Zone | null = null;
  for (const z of zones) {
    if (haversineM(lat, lon, z.center_lat, z.center_lon) <= z.radius_m && (!best || z.radius_m < best.radius_m)) {
      best = z;
    }
  }
  return best;
}

export type Direction8 = 'front' | 'front_right' | 'right' | 'rear_right' | 'rear' | 'rear_left' | 'left' | 'front_left';

/** Bearing relative to machine front → one of 8 sectors (§8.4). */
export function sectorOf(bearingDeg: number): Direction8 {
  const b = ((bearingDeg % 360) + 360) % 360;
  const sectors: Direction8[] = ['front', 'front_right', 'right', 'rear_right', 'rear', 'rear_left', 'left', 'front_left'];
  return sectors[Math.floor(((b + 22.5) % 360) / 45)] as Direction8;
}

export function inSector(bearingDeg: number, [from, to]: [number, number]): boolean {
  const b = ((bearingDeg % 360) + 360) % 360;
  return from <= to ? b >= from && b <= to : b >= from || b <= to;
}

/** §8.10 canonical JSON: keys sorted by UTF-16 code units, undefined omitted, no whitespace. */
export function canonicalJson(value: unknown): string {
  if (value === null || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) throw new Error('canonicalJson: non-finite number');
    return JSON.stringify(value);
  }
  if (typeof value === 'string') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map((v) => canonicalJson(v === undefined ? null : v)).join(',')}]`;
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).filter((k) => obj[k] !== undefined).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalJson(obj[k])}`).join(',')}}`;
}

export function isoMs(ts: number): string {
  return new Date(ts).toISOString();
}

export function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}
