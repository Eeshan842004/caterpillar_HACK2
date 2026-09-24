// Safe Exit Guard (technical spec §8.2, product F6 "Safe Exit Guard", F6-R6…R9, TC-72).
// Advisory only: there is no machine-control port anywhere in the engine (§8.16.1).
import type { Alert, AlertManager } from '../alerts';
import type { SignalStore } from '../state';
import type { MachineProfile, MachineState, SignalName } from '../types';

export type ChecklistStatus = 'confirmed' | 'not_yet' | 'unavailable';

export interface SafeExitView {
  active: boolean;
  exit_cue: 'seat_vacant' | 'door_open' | 'both' | null;
  checklist: { implement_neutral: ChecklistStatus; secure_signal: ChecklistStatus; motion_stopped: ChecklistStatus };
  unavailable_signals: SignalName[];
  secure_signal: SignalName;
}

export class SafeExitGuard {
  private tBelt: number | null = null;
  private lastBelt: boolean | null = null;
  private alert: Alert | null = null;
  view: SafeExitView;

  constructor(private readonly profile: MachineProfile, private readonly alerts: AlertManager) {
    this.view = {
      active: false, exit_cue: null, unavailable_signals: [], secure_signal: profile.secure_signal,
      checklist: { implement_neutral: 'unavailable', secure_signal: 'unavailable', motion_stopped: 'unavailable' },
    };
  }

  evaluate(store: SignalStore, state: MachineState, now: number): void {
    const cfg = this.profile.safe_exit;
    const S = this.profile.secure_signal;
    const belt = store.bool('seatbelt_fastened', now);
    if (belt === false && this.lastBelt === true) this.tBelt = now;     // fresh true→false transition
    if (belt !== null) this.lastBelt = belt;

    const seatVacant = store.bool('seat_occupied', now) === false;
    const doorOpen = store.bool('cab_door_open', now) === true;
    const withinWindow = this.tBelt !== null && now - this.tBelt <= cfg.exit_intent_window_s * 1000;
    const exitIntent = withinWindow && (seatVacant || doorOpen);           // belt-off alone never qualifies (F6-R7)
    const securedState = state === 'SECURED' || state === 'OFF';

    this.view = this.buildView(store, now, seatVacant, doorOpen);

    if (!this.alert && exitIntent && !securedState) {
      const cue = seatVacant && doorOpen ? 'both' : seatVacant ? 'seat_vacant' : 'door_open';
      this.alert = this.alerts.raise('A-EXIT-UNSEC', 'ADVISORY', 'safe_exit', {
        safe_exit: {
          belt_transition_at: this.tBelt, exit_cue: cue, unavailable_signals: this.view.unavailable_signals,
        },
      }, now);
      this.view.exit_cue = cue;
    }
    if (this.alert) {
      const seatBack = store.bool('seat_occupied', now) === true && store.bool('cab_door_open', now) === false;
      if (securedState) this.close('secured', now);
      else if (seatBack) this.close('seat_and_door_restored', now);
    }
    this.view.active = this.alert !== null;
  }

  /** Operator acknowledges "Not exiting" (SAFE_EXIT_CANCEL). */
  cancel(now: number): void {
    if (!this.alert) return;
    this.alerts.ackAlert(this.alert, now);
    this.close('not_exiting', now);
  }

  private close(reason: 'secured' | 'seat_and_door_restored' | 'not_exiting', now: number): void {
    this.alerts.clear('safe_exit', reason, now);
    this.alert = null;
    this.tBelt = null;                 // a new belt transition is needed to raise again
    this.view.active = false;
  }

  private buildView(store: SignalStore, now: number, seatVacant: boolean, doorOpen: boolean): SafeExitView {
    const S = this.profile.secure_signal;
    const guardInputs: SignalName[] = ['seatbelt_fastened', 'seat_occupied', 'cab_door_open', 'implement_neutral', 'ground_speed_kmh', S];
    const unavailable = guardInputs.filter((n) => !store.fresh(n, now));
    const neutral = store.bool('implement_neutral', now);
    const secure = store.bool(S, now);
    const speed = store.num('ground_speed_kmh', now);
    return {
      active: this.alert !== null,
      exit_cue: this.alert ? (seatVacant && doorOpen ? 'both' : seatVacant ? 'seat_vacant' : doorOpen ? 'door_open' : null) : null,
      unavailable_signals: unavailable,
      secure_signal: S,
      checklist: {
        implement_neutral: neutral === null ? 'unavailable' : neutral ? 'confirmed' : 'not_yet',
        secure_signal: secure === null ? 'unavailable' : secure ? 'confirmed' : 'not_yet',
        motion_stopped: speed === null ? 'unavailable' : speed < this.profile.safe_exit.motion_stop_kmh ? 'confirmed' : 'not_yet',
      },
    };
  }
}
