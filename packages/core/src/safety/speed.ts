// Overspeed (technical spec §8.5): speed above the zone limit for ≥ overspeed_hold_s → A-SPEED WARNING.
import type { AlertManager } from '../alerts';
import type { SignalStore } from '../state';
import { zoneAt } from '../util';
import type { MachineProfile, Zone } from '../types';

export class SpeedRules {
  private overSince: number | null = null;
  private underCount = 0;
  limit: number | null = null;
  speed: number | null = null;
  zoneId: string | null = null;

  constructor(private readonly profile: MachineProfile, private readonly alerts: AlertManager, private readonly zones: Zone[]) {}

  evaluate(store: SignalStore, now: number): void {
    const cfg = this.profile.speed;
    this.speed = store.num('ground_speed_kmh', now);
    if (!cfg) return;
    const lat = store.num('lat', now);
    const lon = store.num('lon', now);
    const zone = lat !== null && lon !== null ? zoneAt(lat, lon, this.zones) : null;
    this.zoneId = zone?.zone_id ?? null;
    this.limit = zone?.speed_limit_kmh ?? cfg.default_limit_kmh;
    if (this.speed === null) return;
    if (this.speed > this.limit) {
      this.underCount = 0;
      this.overSince ??= now;
      if (now - this.overSince >= cfg.overspeed_hold_s * 1000) {
        this.alerts.raise('A-SPEED', 'WARNING', 'speed', { speed_kmh: this.speed, limit_kmh: this.limit, zone_id: this.zoneId }, now);
      }
    } else {
      this.overSince = null;
      this.underCount += 1;
      if (this.underCount >= 3) this.alerts.clear('speed', 'below_limit', now);
    }
  }
}
