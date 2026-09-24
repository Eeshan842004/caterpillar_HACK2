// Seatbelt rules (technical spec §8.2, F6-R1…R5, R10…R14).
import type { AlertManager } from '../alerts';
import type { SignalStore } from '../state';
import type { MachineProfile, MachineState } from '../types';

export type BeltPill = 'fastened' | 'unfastened' | 'unavailable';

export class SeatbeltRules {
  private consecutive = { MOVE: 0, OPER: 0, UNAV: 0 };
  private flapChanges: number[] = [];
  private lastBelt: boolean | null = null;
  private flapReported = false;
  pill: BeltPill = 'unavailable';
  /** Private per-shift compliance (A12, F6-R3): seconds fastened / unfastened while operating. */
  compliance = { fastened_s: 0, unfastened_s: 0 };

  constructor(private readonly profile: MachineProfile, private readonly alerts: AlertManager) {}

  /** Returns 'belt_switch_flapping' once per shift when the switch flaps while secured (F6-R4, machine check). */
  evaluate(store: SignalStore, state: MachineState, now: number): 'belt_switch_flapping' | null {
    const S = this.profile.secure_signal;
    if (state === 'OFF') {
      this.alerts.clearWhere((a) => a.group_key === 'belt' || a.group_key === 'belt_unav', 'engine_off', now);
      this.consecutive = { MOVE: 0, OPER: 0, UNAV: 0 };
      this.pill = store.fresh('seatbelt_fastened', now) ? (store.value('seatbelt_fastened') ? 'fastened' : 'unfastened') : 'unavailable';
      return null;
    }
    const beltFresh = store.fresh('seatbelt_fastened', now);
    if (!beltFresh || (!store.fresh(S, now) && state !== 'TRAVELLING')) {
      this.alerts.clear('belt', 'signal_unavailable', now);
      this.consecutive.MOVE = this.consecutive.OPER = 0;
      this.consecutive.UNAV += 1;
      if (this.consecutive.UNAV >= 2) this.alerts.raise('A-BELT-UNAV', 'INFO', 'belt_unav', {}, now);
      this.pill = 'unavailable';
      return null;
    }
    this.consecutive.UNAV = 0;
    this.alerts.clear('belt_unav', 'signal_restored', now);

    const belt = store.value('seatbelt_fastened') === true;
    this.pill = belt ? 'fastened' : 'unfastened';
    if (state === 'WORKING' || state === 'READY' || state === 'TRAVELLING') {
      if (belt) this.compliance.fastened_s += 1;
      else this.compliance.unfastened_s += 1;
    }

    let cond: 'MOVE' | 'OPER' | null = null;
    if (!belt && state === 'TRAVELLING') cond = 'MOVE';
    else if (!belt && (state === 'WORKING' || state === 'READY')) cond = 'OPER';
    else if (!belt && state === 'UNKNOWN' && store.bool('engine_on', now) === true) cond = 'OPER'; // F6-R14

    if (cond === 'MOVE') {
      this.consecutive.MOVE += 1;
      this.consecutive.OPER = 0;
    } else if (cond === 'OPER') {
      this.consecutive.OPER += 1;
      this.consecutive.MOVE = 0;
    } else {
      this.consecutive.MOVE = this.consecutive.OPER = 0;
    }

    const debounce = this.profile.seatbelt.debounce_s;
    if (cond === 'MOVE' && this.consecutive.MOVE >= debounce) {
      this.alerts.raise('A-BELT-MOVE', 'CRITICAL', 'belt', {}, now);
    } else if (cond === 'OPER' && this.consecutive.OPER >= debounce) {
      const current = this.alerts.byGroupKey('belt');
      if (current && current.alert_type === 'A-BELT-MOVE' && current.status !== 'CLEARED') {
        this.alerts.clear('belt', 'downgrade', now);         // MOVE → OPER is clear + raise (§8.2)
      }
      this.alerts.raise('A-BELT-OPER', 'WARNING', 'belt', {}, now);
    } else if (cond === null) {
      this.alerts.clear('belt', 'belt_fastened_or_secured', now);
    }

    // Belt switch flapping while secured → machine check, never an operator alert
    if (state === 'SECURED') {
      if (this.lastBelt !== null && this.lastBelt !== belt) this.flapChanges.push(now);
      const window = this.profile.seatbelt.flap_window_s * 1000;
      this.flapChanges = this.flapChanges.filter((t) => now - t <= window);
    }
    this.lastBelt = belt;
    if (!this.flapReported && this.flapChanges.length > this.profile.seatbelt.flap_changes) {
      this.flapReported = true;
      return 'belt_switch_flapping';
    }
    return null;
  }
}
