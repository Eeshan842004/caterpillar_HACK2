// Idle detection and classification (technical spec §8.7, §7.4.3; product F9).
import type { SignalStore } from '../state';
import { idleCategory, type IdleCategory, type IdleClass, type IdleReason, type MachineProfile, type MachineState } from '../types';

export type IdlePhase = 'CANDIDATE' | 'RECORDED' | 'PROMPTING' | 'UNEXPLAINED' | 'EXPLAINED';

export interface IdleEvent {
  idle_event_id: string;
  phase: IdlePhase;
  t0: number;
  recorded: boolean;
  required_s: number;
  elapsed_s: number;
  reason: IdleReason | null;
  reason_entry_id: string | null;
  prompted_at: number | null;
  task_id: string | null;
  basis: 'warmup' | 'cooldown' | 'regen' | 'mixed' | 'none';
}

export interface IdleEnded {
  event: IdleEvent;
  end: number;
  duration_s: number;
  idle_class: IdleClass;
  category: IdleCategory | null;
  non_required_s: number;
}

export type IdleSignal =
  | { type: 'recorded'; event: IdleEvent }
  | { type: 'prompt'; event: IdleEvent }
  | { type: 'prompt_expired'; event: IdleEvent }
  | { type: 'ended'; ended: IdleEnded }
  | { type: 'discarded' };

export class IdleTracker {
  current: IdleEvent | null = null;
  private loadHistory: { ts: number; load: number }[] = [];
  private engineStartedAt: number | null = null;
  private coolantAtT0: number | null = null;

  constructor(private readonly profile: MachineProfile, private readonly newId: () => string) {}

  /** Evaluated once per tick after the machine state update. */
  tick(store: SignalStore, state: MachineState, now: number, activeTaskId: string | null): IdleSignal[] {
    const cfg = this.profile.idle;
    const out: IdleSignal[] = [];
    const engineOn = store.bool('engine_on', now);
    const load = store.num('load_factor_pct', now);
    if (engineOn === true && this.engineStartedAt === null) this.engineStartedAt = now;
    if (engineOn === false) this.engineStartedAt = null;
    if (load !== null) {
      this.loadHistory.push({ ts: now, load });
      const cut = now - cfg.cooldown_lookback_s * 1000;
      while (this.loadHistory.length && (this.loadHistory[0] as { ts: number }).ts < cut) this.loadHistory.shift();
    }

    const idleState = engineOn === true && (state === 'SECURED' || state === 'READY');
    if (!idleState) {
      if (this.current) {
        const ev = this.current;
        this.current = null;
        if (!ev.recorded) out.push({ type: 'discarded' });
        else out.push({ type: 'ended', ended: this.finish(ev, now) });
      }
      return out;
    }

    if (!this.current) {
      const before = this.loadHistory.filter((s) => s.ts < now);
      const avgLoad = before.length ? before.reduce((a, s) => a + s.load, 0) / before.length : 0;
      this.coolantAtT0 = store.num('coolant_temp_c', now);
      this.current = {
        idle_event_id: this.newId(), phase: 'CANDIDATE', t0: now, recorded: false, required_s: 0, elapsed_s: 0,
        reason: null, reason_entry_id: null, prompted_at: null, task_id: activeTaskId,
        basis: avgLoad >= cfg.cooldown_trigger_load_pct ? 'cooldown' : 'none',
      };
    }
    const ev = this.current;
    ev.elapsed_s = Math.round((now - ev.t0) / 1000);
    ev.required_s = this.requiredSeconds(ev, store, now);
    const nonRequired = ev.elapsed_s - ev.required_s;

    if (!ev.recorded && (ev.elapsed_s >= cfg.threshold_s || ev.reason)) {
      ev.recorded = true;
      ev.phase = ev.reason ? 'EXPLAINED' : 'RECORDED';
      out.push({ type: 'recorded', event: ev });
    }
    if (ev.recorded && ev.phase === 'RECORDED' && nonRequired >= cfg.threshold_s && !ev.reason) {
      ev.phase = 'PROMPTING';
      ev.prompted_at = now;
      out.push({ type: 'prompt', event: ev });
    }
    if (ev.phase === 'PROMPTING' && ev.prompted_at !== null && now - ev.prompted_at >= cfg.prompt_timeout_s * 1000) {
      ev.phase = 'UNEXPLAINED';                    // asked once, not repeated (F9-R2)
      out.push({ type: 'prompt_expired', event: ev });
    }
    return out;
  }

  /** Operator gives a reason (prompt answer, early voice report, or later from A3). */
  setReason(reason: IdleReason, entryId: string): IdleEvent | null {
    if (!this.current) return null;
    this.current.reason = reason;
    this.current.reason_entry_id = entryId;
    if (this.current.recorded) this.current.phase = 'EXPLAINED';
    return this.current;
  }

  private requiredSeconds(ev: IdleEvent, store: SignalStore, now: number): number {
    const cfg = this.profile.idle;
    let required = 0;
    if (ev.basis === 'cooldown') required = Math.min(ev.elapsed_s, cfg.cooldown_required_s);
    if (this.coolantAtT0 !== null && this.coolantAtT0 < cfg.warmup_coolant_c && this.engineStartedAt !== null
      && ev.t0 - this.engineStartedAt <= cfg.warmup_max_s * 1000) {
      const coolant = store.num('coolant_temp_c', now);
      const warmEnd = Math.min(this.engineStartedAt + cfg.warmup_max_s * 1000, coolant !== null && coolant >= cfg.warmup_coolant_c ? now : Number.POSITIVE_INFINITY);
      required = Math.max(required, Math.round((Math.min(now, warmEnd) - ev.t0) / 1000));
      if (ev.basis === 'none') ev.basis = 'warmup';
      else if (ev.basis === 'cooldown') ev.basis = 'mixed';
    }
    return Math.max(0, Math.min(required, ev.elapsed_s));
  }

  private finish(ev: IdleEvent, now: number): IdleEnded {
    const duration = Math.round((now - ev.t0) / 1000);
    const nonRequired = Math.max(0, duration - ev.required_s);
    let idleClass: IdleClass;
    if (ev.reason) idleClass = 'reported';
    else if (nonRequired < this.profile.idle.threshold_s) idleClass = 'required';
    else idleClass = 'unexplained';
    return {
      event: ev, end: now, duration_s: duration, idle_class: idleClass, non_required_s: nonRequired,
      category: ev.reason ? idleCategory(ev.reason) : null,
    };
  }
}
