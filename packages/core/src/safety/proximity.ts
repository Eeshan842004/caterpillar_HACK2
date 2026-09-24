// Proximity rules (technical spec §8.4, F7-R1…R9, SD-09).
import type { AlertManager } from '../alerts';
import type { SignalStore } from '../state';
import { inSector, sectorOf } from '../util';
import type { AlertLevel, DetectionEvent, MachineProfile, ProximityHeartbeat } from '../types';

export type ProximityPill =
  | { status: 'clear' }
  | { status: 'unavailable' }
  | { status: 'alert'; level: AlertLevel; object_type: DetectionEvent['type']; place: string; distance_m: number };

interface Track {
  event: DetectionEvent;
  noneCount: number;
}

export function ttcSeconds(distance_m: number, closing_mps: number, closingMin: number): number {
  return closing_mps > closingMin ? distance_m / closing_mps : Number.POSITIVE_INFINITY;
}

/** Level for one object (§8.4 pseudo-code). `inMotion` = speed > 0.5 or swing/implement active. */
export function proximityLevel(
  ev: DetectionEvent,
  profile: MachineProfile,
  multiplier: number,
  inMotion: boolean,
  travelDirection: 'forward' | 'reverse' | 'none',
): AlertLevel | null {
  const p = profile.proximity;
  let inner: number;
  let outer: number | null;
  if (p.mode === 'radial') {
    inner = p.inner_m * multiplier;
    outer = p.outer_m * multiplier;
  } else if (travelDirection === 'none') {
    inner = p.stationary_inner_m * multiplier;
    outer = null;
  } else {
    const cfg = travelDirection === 'reverse' ? p.reverse : p.forward;
    if (!inSector(ev.bearing_deg, cfg.sector_deg)) return null;
    inner = cfg.inner_m * multiplier;
    outer = cfg.outer_m * multiplier;
  }
  const ttcC = p.ttc_caution_s * multiplier;
  const ttcW = p.ttc_warning_s * multiplier;
  const ttc = ttcSeconds(ev.distance_m, ev.closing_mps, p.closing_min_mps);
  const departing = ev.closing_mps < p.departing_mps;
  if (ev.type === 'person' && ev.distance_m <= inner && inMotion) return 'CRITICAL'; // SD-09: even if departing
  if (departing) return null;
  if (ev.type === 'structure') return ttc < ttcW ? 'WARNING' : ttc < ttcC ? 'CAUTION' : null;
  if (ev.distance_m <= inner || ttc < ttcW) return 'WARNING';
  if ((outer !== null && ev.distance_m <= outer) || ttc < ttcC) return 'CAUTION';
  return null;
}

const TYPE_BY_LEVEL = { CAUTION: 'A-PROX-CAUT', WARNING: 'A-PROX-WARN', CRITICAL: 'A-PROX-CRIT' } as const;

export class ProximityRules {
  private tracks = new Map<string, Track>();
  private heartbeat: ProximityHeartbeat | null = null;
  pill: ProximityPill = { status: 'unavailable' };

  constructor(private readonly profile: MachineProfile, private readonly alerts: AlertManager) {}

  ingest(events: DetectionEvent[], heartbeat: ProximityHeartbeat | null): void {
    if (heartbeat) this.heartbeat = heartbeat;
    for (const ev of events) {
      const t = this.tracks.get(ev.object_id);
      this.tracks.set(ev.object_id, { event: ev, noneCount: t?.noneCount ?? 0 });
    }
  }

  /** Returns object alerts that reached WARNING/CRITICAL this tick (incident trigger, F7-R4). */
  evaluate(store: SignalStore, multiplier: number, now: number): string[] {
    const p = this.profile.proximity;
    const hb = this.heartbeat;
    if (!hb || now - hb.ts > p.heartbeat_stale_ms || hb.quality < p.min_quality) {
      this.alerts.raise('A-PROX-UNAV', 'CAUTION', 'prox_unav', {}, now);
      this.alerts.clearWhere((a) => a.group_key.startsWith('prox:'), 'monitoring_unavailable', now);
      this.tracks.clear();
      this.pill = { status: 'unavailable' };
      return [];
    }
    this.alerts.clear('prox_unav', 'heartbeat_restored', now);

    const speed = store.num('ground_speed_kmh', now) ?? 0;
    const inMotion = speed > 0.5 || store.bool('swing_active', now) === true || store.bool('implement_active', now) === true;
    const dirRaw = store.value('travel_direction');
    const direction = dirRaw === 'forward' || dirRaw === 'reverse' ? dirRaw : 'none';
    const escalated: string[] = [];
    let worst: ProximityPill = { status: 'clear' };
    const rank = { CAUTION: 1, WARNING: 2, CRITICAL: 3, INFO: 0, ADVISORY: 0 } as Record<AlertLevel, number>;

    for (const [id, track] of this.tracks) {
      const ev = track.event;
      const group = `prox:${id}`;
      if (now - ev.ts > 1000) {                       // object gone
        this.tracks.delete(id);
        this.alerts.clear(group, 'object_gone', now);
        continue;
      }
      if (ev.quality < p.min_quality) continue;
      const level = proximityLevel(ev, this.profile, multiplier, inMotion, direction);
      if (level === null) {
        track.noneCount += 1;
        if (track.noneCount >= p.clear_after_s) this.alerts.clear(group, 'object_clear', now);
        continue;
      }
      track.noneCount = 0;
      const place = sectorOf(ev.bearing_deg);
      const ttc = ttcSeconds(ev.distance_m, ev.closing_mps, p.closing_min_mps);
      const before = this.alerts.byGroupKey(group);
      const beforeLevel = before && before.status !== 'CLEARED' ? before.level : null;
      this.alerts.raise(TYPE_BY_LEVEL[level as 'CAUTION' | 'WARNING' | 'CRITICAL'], level, group, {
        object_id: id, object_type: ev.type, place, distance_m: Math.round(ev.distance_m * 10) / 10,
        ttc_s: Number.isFinite(ttc) ? Math.round(ttc * 10) / 10 : null, multiplier,
      }, now);
      if ((level === 'WARNING' || level === 'CRITICAL') && (!beforeLevel || rank[beforeLevel] < 2)) escalated.push(group);
      if (worst.status !== 'alert' || rank[level] > rank[worst.level]) {
        worst = { status: 'alert', level, object_type: ev.type, place, distance_m: Math.round(ev.distance_m * 10) / 10 };
      }
    }
    this.pill = worst;
    return escalated;
  }
}
