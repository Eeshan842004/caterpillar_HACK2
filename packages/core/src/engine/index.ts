// ShiftEngine — orchestrates rules, tasks, idle review and the ledger (technical spec §8.16).
// Pure: time comes from the injected clock, ids from the injected generator. No machine-control port exists.
import { type Alert, AlertManager, type BudgetHour, type SpeechOut } from '../alerts';
import { hashPin, isLocked, type LockoutState, registerFailure, verifyPin } from '../auth';
import { effectiveConditions, type ConditionName, type ConditionReport, type EffectiveConditions, forecastAt } from '../safety/conditions';
import { type BeltPill, SeatbeltRules } from '../safety/seatbelt';
import { SafeExitGuard, type SafeExitView } from '../safety/safeExitGuard';
import { ProximityRules, type ProximityPill } from '../safety/proximity';
import { SpeedRules } from '../safety/speed';
import { type EstimatorArtifact, type LiveResult, type TaskEstimate, baselineMinutes, estimateTask, expectedWaitMin, liveUpdate, taskFeatures } from '../estimate';
import { IdleTracker, type IdleEvent } from '../idle';
import { Ledger, type LedgerStore } from '../ledger';
import { MachineStateMachine, SignalStore } from '../state';
import { type Accounting, type IdleSpan, type ImpactSummary, type Interval, TaskTransitionError, impactPreview, nextPlannedTask, nextTaskState, timeAccounting } from '../tasks';
import {
  type BlockReason, type DetectionEvent, type ForecastHour, type HandoverItemRef, type IdleReason, type LedgerEntry,
  type MachineProfile, type MachineRef, type MachineState, type OperatorRef, type ProximityHeartbeat, type ReassignReason,
  type SignalName, type SignalSample, type Site, type TaskAssignment, type TaskState, type Zone, idleCategory,
} from '../types';
import { type Clock, HOUR, MINUTE, formatHHMM, timeOfDayBand, toLocal, zoneAt } from '../util';

// ------------------------------------------------------------------------------------------------ public types

export interface EngineInit {
  profile: MachineProfile;
  site: Site;
  zones: Zone[];
  machine: MachineRef;
  operators: OperatorRef[];
  assignments: TaskAssignment[];
  forecast: ForecastHour[];
  handoverItems: HandoverItemRef[];
  history: LedgerEntry[];
  artifact: EstimatorArtifact | null;
  device_id: string;
  data_origin: string;
  clock: Clock;
  newId: () => string;
  store: LedgerStore;
}

export type PromptType = 'idle_reason' | 'block_reason' | 'reassign_reason' | 'complete_output' | 'notice';

export interface PromptOption {
  key: string;
  label: string;
}

export interface Prompt {
  prompt_id: string;
  type: PromptType;
  title: string;
  body?: string;
  options: PromptOption[];
  dismissible: boolean;
  created_at: number;
  expires_at: number | null;
  context: Record<string, unknown>;
  deferred_counted?: boolean;
}

export type Command =
  | { type: 'SIGN_IN'; operator_id: string; pin: string }
  | { type: 'SIGN_IN_FOB'; operator_id: string }
  | { type: 'ACK_HANDOVER'; item_id: string | 'all' }
  | { type: 'TASK_START'; task_id: string }
  | { type: 'TASK_PAUSE'; task_id: string }
  | { type: 'TASK_RESUME'; task_id: string }
  | { type: 'TASK_BLOCK'; task_id: string; reason: BlockReason }
  | { type: 'TASK_COMPLETE'; task_id: string; output_qty: number }
  | { type: 'TASK_REQUEST_REASSIGN'; task_id: string; reason: ReassignReason }
  | { type: 'TASK_NOTIFY_SUPERVISOR'; task_id: string }
  | { type: 'IDLE_REASON'; reason: IdleReason; via: 'button' | 'voice'; original_text?: string }
  | { type: 'CORRECT_LAST_REASON'; reason: IdleReason }
  | { type: 'ALERT_ACK' }
  | { type: 'SAFE_EXIT_CANCEL' }
  | { type: 'PROMPT_ANSWER'; prompt_id: string; option: string }
  | { type: 'PROMPT_DISMISS'; prompt_id: string }
  | { type: 'OPEN_PROMPT'; prompt: 'block_reason' | 'reassign_reason' | 'complete_output'; task_id: string }
  | { type: 'CONDITION_REPORT'; condition: ConditionName; active: boolean }
  | { type: 'DISMISS_IMPACT' }
  | { type: 'END_SHIFT' };

export interface CommandResult {
  ok: boolean;
  message?: string;
}

export interface TaskView {
  task: TaskAssignment;
  state: TaskState;
  is_next: boolean;
  estimate: TaskEstimate;
  expected_wait_min: number;
  live: LiveResult | null;
  accounting: Accounting | null;
  progress: number;
  blocker: BlockReason | null;
  pending_request: 'reassignment' | 'supervisor_notification' | null;
  unfamiliar: boolean;
  zone_name: string | null;
}

export interface BriefingView {
  handover: (HandoverItemRef & { acknowledged: boolean })[];
  all_acknowledged: boolean;
  risk_notes: string[];
  conditions_text: string;
  conditions_old: boolean;
  task_count: number;
}

export interface EngineSnapshot {
  now: number;
  local_time: string;
  site: Site;
  machine: MachineRef & { state: MachineState; state_since: number; display_name: string };
  shift: { shift_id: string; operator: OperatorRef; guidance: 'guided' | 'concise'; started_at: number } | null;
  signal_health: { name: SignalName; fresh: boolean; age_ms: number | null }[];
  conditions: EffectiveConditions;
  alerts: { active: Alert[]; top: Alert | null; budget: BudgetHour[] };
  safe_exit: SafeExitView;
  belt: BeltPill;
  proximity: ProximityPill;
  speed: { speed_kmh: number | null; limit_kmh: number | null; over: boolean };
  prompt: Prompt | null;
  prompts_waiting: number;
  tasks: TaskView[];
  active_task_id: string | null;
  day_finish: { p50_at: number; p90_at: number } | null;
  impact: ImpactSummary | null;
  idle: (IdleEvent & { non_required_s: number }) | null;
  briefing: BriefingView;
  ledger_count: number;
  pending_sync: number;
  pin_lockout_until: Record<string, number>;
  illustrative_notice: string;
}

// ------------------------------------------------------------------------------------------------ engine

interface TaskRun {
  task: TaskAssignment;
  state: TaskState;
  intervals: Interval[];
  blocker: BlockReason | null;
  startEstimate: TaskEstimate | null;
  progressStart: { units: number; cycles: number } | null;
  pendingRequest: 'reassignment' | 'supervisor_notification' | null;
}

interface IdleRecord {
  idle_event_id: string;
  start: number;
  end: number | null;
  reason_entry_id: string | null;
  category: IdleSpan['category'];
  task_id: string | null;
}

const REASON_LABEL: Record<IdleReason, string> = {
  waiting_truck: 'Waiting for truck', waiting_loader: 'Waiting for loader', shovel_queue: 'Shovel queue',
  crusher_queue: 'Crusher queue', access_blocked: 'Access blocked', instructed_hold: 'Instructed to hold',
  break: 'Break', other: 'Other',
};
const BLOCK_LABEL: Record<BlockReason, string> = {
  access_blocked: 'Access blocked', utility_mark: 'Utility mark', waiting_instruction: 'Waiting for instruction',
  machine_fault: 'Machine fault', weather: 'Weather', other: 'Other',
};
const REASSIGN_LABEL: Record<ReassignReason, string> = {
  machine_fault: 'Machine fault', not_trained: 'Not trained for this', access_blocked: 'Access blocked',
  wrong_machine: 'Wrong machine', other: 'Other',
};
export const LABELS = { REASON_LABEL, BLOCK_LABEL, REASSIGN_LABEL };

export class ShiftEngine {
  readonly profile: MachineProfile;
  private readonly init: EngineInit;
  private readonly store: SignalStore;
  private readonly sm: MachineStateMachine;
  readonly alerts: AlertManager;
  private readonly seatbelt: SeatbeltRules;
  private readonly safeExit: SafeExitGuard;
  private readonly proximity: ProximityRules;
  private readonly speed: SpeedRules;
  private readonly idle: IdleTracker;
  readonly ledger: Ledger;
  private shift: EngineSnapshot['shift'] = null;
  private handoverId: string | null = null;
  private runs: TaskRun[];
  private idleRecords: IdleRecord[] = [];
  private prompts: Prompt[] = [];
  private conditionReports: ConditionReport[] = [];
  private acked = new Set<string>();
  private impact: ImpactSummary | null = null;
  private lastReasonEntry: LedgerEntry | null = null;
  private lockouts: Record<string, LockoutState> = {};
  private lastFinish50: number | null = null;
  /** P50 finish of the active task just before the current delay began (idle start / block) — §8.6.9 "before". */
  private finishBeforeDelay: number | null = null;
  private lastTickTs: number | null = null;

  constructor(init: EngineInit) {
    this.init = init;
    this.profile = init.profile;
    const now = init.clock.now();
    this.store = new SignalStore(init.profile);
    this.sm = new MachineStateMachine(init.profile, now);
    this.ledger = new Ledger(init.store, {
      device_id: init.device_id, machine_id: init.machine.machine_id, data_origin: init.data_origin, newId: init.newId,
      now: () => init.clock.now(),
    });
    const rulePrefix = `profile=${init.profile.profile_id}@${init.profile.version}`;
    this.alerts = new AlertManager(init.newId, (subtype, a, source) => {
      this.append({
        kind: 'alert', subtype, source, observed_at: this.init.clock.now(), rule_or_model_version: `${a.alert_type.toLowerCase()}@1;${rulePrefix}`,
        payload: {
          alert_id: a.alert_id, alert_type: a.alert_type, level: a.level, group_key: a.group_key, zone_id: a.zone_id ?? null,
          object_id: a.object_id ?? null, object_type: a.object_type ?? null, place: a.place ?? null,
          distance_m: a.distance_m ?? null, ttc_s: a.ttc_s ?? null, multiplier: a.multiplier ?? null,
          occurrences: a.occurrences, clear_reason: subtype === 'cleared' ? a.clear_reason ?? null : null,
          safe_exit: a.alert_type === 'A-EXIT-UNSEC' ? a.safe_exit ?? null : null,
        },
      });
    }, init.profile.machine_class);
    this.seatbelt = new SeatbeltRules(init.profile, this.alerts);
    this.safeExit = new SafeExitGuard(init.profile, this.alerts);
    this.proximity = new ProximityRules(init.profile, this.alerts);
    this.speed = new SpeedRules(init.profile, this.alerts, init.zones);
    this.idle = new IdleTracker(init.profile, init.newId);
    this.runs = init.assignments
      .filter((t) => t.status === 'assigned' && t.machine_id === init.machine.machine_id)
      .sort((a, b) => a.planned_date.localeCompare(b.planned_date) || a.sequence - b.sequence)
      .map((task) => ({ task, state: 'PLANNED', intervals: [], blocker: null, startEstimate: null, progressStart: null, pendingRequest: null }));
    // Handover items that name a blocked task arrive BLOCKED on the board (J1: "Trench T2 blocked by utility mark")
    for (const item of init.handoverItems) {
      const run = item.item_type === 'blocked_task' && item.task_id ? this.runs.find((r) => r.task.task_id === item.task_id) : undefined;
      if (run && run.state === 'PLANNED') {
        run.state = 'BLOCKED';
        run.blocker = 'utility_mark';
      }
    }
  }

  // ---------------------------------------------------------------------------------------------- helpers

  private now(): number {
    return this.init.clock.now();
  }

  private append(input: Parameters<Ledger['append']>[0]): LedgerEntry {
    return this.ledger.append(input, this.shift?.shift_id ?? null, this.shift?.operator.operator_id ?? null);
  }

  private operator(id: string): OperatorRef | undefined {
    return this.init.operators.find((o) => o.operator_id === id);
  }

  private run(taskId: string): TaskRun {
    const r = this.runs.find((x) => x.task.task_id === taskId);
    if (!r) throw new TaskTransitionError('Unknown task');
    return r;
  }

  private activeRun(): TaskRun | undefined {
    return this.runs.find((r) => r.state === 'ACTIVE') ?? this.runs.find((r) => r.state === 'PAUSED' || r.state === 'BLOCKED' && r.intervals.length > 0);
  }

  private conditions(now: number): EffectiveConditions {
    return effectiveConditions(now, this.init.site, this.profile, this.init.forecast, this.conditionReports);
  }

  private experienceMonths(op: OperatorRef, now: number): number {
    const hired = Date.parse(`${op.hired_at}T00:00:00Z`);
    const monthsFromDate = Math.floor((now - hired) / (30.44 * 24 * HOUR));
    return Math.max(op.experience_months, Math.max(0, monthsFromDate));
  }

  private estimateContext(task: TaskAssignment, now: number) {
    const planned = task.planned_start_at !== null && task.planned_start_at > now ? task.planned_start_at : now;
    const hour = forecastAt(this.init.forecast, planned);
    const cond = effectiveConditions(planned, this.init.site, this.profile, this.init.forecast, this.conditionReports);
    const weather = cond.rain ? 'rain' : cond.dust ? 'dusty' : hour && hour.visibility_m !== null && hour.visibility_m < 1000 ? 'foggy'
      : hour && hour.wind_kmh >= 38 ? 'windy' : 'clear';
    let visibility = hour?.visibility_m == null ? 'good' : hour.visibility_m >= 5000 ? 'good' : hour.visibility_m >= 1000 ? 'moderate' : 'poor';
    if (cond.darkness && visibility === 'good') visibility = 'moderate';
    const t = hour?.temp_c;
    const temperature_band = t == null ? 'mild' : t < 20 ? 'cool' : t < 30 ? 'mild' : t <= 38 ? 'hot' : 'extreme';
    return {
      weather, visibility, temperature_band, time_of_day: timeOfDayBand(planned, this.init.site.utc_offset_minutes),
      site_congestion: this.init.site.congestion_level, darkness: cond.darkness,
      year: Number(toLocal(planned, this.init.site.utc_offset_minutes).date.slice(0, 4)),
    };
  }

  private estimateFor(run: TaskRun, now: number): { estimate: TaskEstimate; context: ReturnType<ShiftEngine['estimateContext']> } {
    const op = this.shift?.operator ?? this.init.operators[0];
    const ctx = this.estimateContext(run.task, now);
    const baseline = baselineMinutes(this.profile, this.init.site, run.task.task_type, run.task.material, run.task.quantity);
    const features = taskFeatures(run.task, { skill_level: op?.skill_level ?? 'intermediate', experience_months: op ? this.experienceMonths(op, now) : 0 },
      this.init.machine, ctx);
    return { estimate: estimateTask(baseline, features, this.init.artifact), context: ctx };
  }

  private recentWaits(taskType: string): number[] {
    // History waits for this site and task type (§8.6.5). History entries carry task ids; types resolve through today's
    // assignments only, so on first launch this falls back to the profile default (documented gap).
    const types = new Map(this.runs.map((r) => [r.task.task_id, r.task.task_type]));
    return [...this.init.history, ...this.ledger.all()]
      .filter((e) => e.kind === 'task_event' && e.subtype === 'complete' && types.get(String(e.payload.task_id)) === taskType)
      .map((e) => Number(e.payload.waiting_min ?? 0));
  }

  private progressOf(run: TaskRun, now: number): number {
    if (!run.progressStart) return 0;
    const tt = this.profile.task_types.find((t) => t.task_type === run.task.task_type);
    const units = Number(this.store.value('progress_units') ?? 0) - run.progressStart.units;
    const cycles = Number(this.store.value('load_cycles') ?? 0) - run.progressStart.cycles;
    void now;
    if (!tt) return 0;
    if (tt.rate_model === 'bucket') {
      const rc = this.profile.rate_constants;
      return Math.max(0, cycles * (rc.bucket_capacity_m3 ?? 0) * (rc.fill_factor?.[run.task.material] ?? 1));
    }
    if (tt.rate_model === 'haul') return Math.max(0, cycles * (this.profile.rate_constants.payload_t ?? 0));
    return Math.max(0, units);
  }

  private idleSpansFor(taskId: string | null): IdleSpan[] {
    return this.idleRecords.filter((r) => taskId === null || r.task_id === taskId)
      .map((r) => ({ start: r.start, end: r.end, category: r.category }));
  }

  private liveFor(run: TaskRun, now: number, overrideSiteDelay?: { expectedTotalMin: number; elapsedMin: number } | null): LiveResult | null {
    const est = run.startEstimate;
    if (!est || est.p10_min === null || est.p50_min === null || est.p90_min === null) return null;
    const acc = timeAccounting(run.intervals, this.idleSpansFor(run.task.task_id), now);
    const expected = expectedWaitMin(this.profile, run.task.task_type, this.recentWaits(run.task.task_type));
    const cur = this.idle.current;
    let siteDelay = overrideSiteDelay ?? null;
    if (siteDelay === undefined || siteDelay === null) {
      if (cur && cur.reason && idleCategory(cur.reason) === 'site_delay') {
        siteDelay = { expectedTotalMin: this.profile.idle.default_expected_wait_min[cur.reason] ?? 10, elapsedMin: cur.elapsed_s / 60 };
      }
    }
    return liveUpdate({
      now, prior: { p10: est.p10_min, p50: est.p50_min, p90: est.p90_min }, quantity: run.task.quantity,
      progress: this.progressOf(run, now), activeElapsedMin: acc.active_min, paused: run.state !== 'ACTIVE',
      expectedWaitMin: expected, waitingSoFarMin: acc.waiting_min, siteDelayInProgress: siteDelay,
    });
  }

  private pushPrompt(p: Omit<Prompt, 'prompt_id' | 'created_at'>): Prompt {
    const prompt: Prompt = { ...p, prompt_id: this.init.newId(), created_at: this.now() };
    this.prompts = this.prompts.filter((x) => x.type !== p.type || p.type === 'notice');
    this.prompts.push(prompt);
    return prompt;
  }

  private dropPrompt(type: PromptType): void {
    this.prompts = this.prompts.filter((p) => p.type !== type);
  }

  // ---------------------------------------------------------------------------------------------- commands

  dispatch(cmd: Command): CommandResult {
    try {
      return this.handle(cmd);
    } catch (err) {
      if (err instanceof TaskTransitionError) return { ok: false, message: err.message };
      throw err;
    }
  }

  private handle(cmd: Command): CommandResult {
    const now = this.now();
    switch (cmd.type) {
      case 'SIGN_IN':
      case 'SIGN_IN_FOB': {
        const op = this.operator(cmd.operator_id);
        if (!op) return { ok: false, message: 'Operator not on this device' };
        if (cmd.type === 'SIGN_IN') {
          if (isLocked(this.lockouts[op.operator_id], now)) return { ok: false, message: 'Locked for 60 s' };
          if (!verifyPin(cmd.pin, op.pin_salt, op.pin_hash, op.pin_iterations)) {
            this.lockouts[op.operator_id] = registerFailure(this.lockouts[op.operator_id] ?? { failures: 0, locked_until: null }, now);
            const locked = isLocked(this.lockouts[op.operator_id], now);
            return { ok: false, message: locked ? 'Locked for 60 s' : 'PIN not recognised' };
          }
          this.lockouts[op.operator_id] = { failures: 0, locked_until: null };
        }
        const guided = now - Date.parse(`${op.hired_at}T00:00:00Z`) < 30 * 24 * HOUR;
        this.shift = { shift_id: this.init.newId(), operator: op, guidance: guided ? 'guided' : 'concise', started_at: now };
        this.handoverId = this.init.newId();
        this.append({ kind: 'shift_event', subtype: 'start', source: 'reported', observed_at: now, payload: {
          auth_method: cmd.type === 'SIGN_IN' ? 'pin' : 'fob_sim', language: op.language, guidance: this.shift.guidance,
          profile_id: this.profile.profile_id, profile_version: this.profile.version } });
        return { ok: true };
      }
      case 'ACK_HANDOVER': {
        const items = this.init.handoverItems.filter((i) => i.status === 'open' && (cmd.item_id === 'all' || i.item_id === cmd.item_id));
        for (const item of items) {
          if (this.acked.has(item.item_id)) continue;
          this.acked.add(item.item_id);
          this.append({ kind: 'handover_item', subtype: 'acknowledged', source: 'reported', observed_at: now, payload: { item_id: item.item_id } });
        }
        return { ok: true };
      }
      case 'TASK_START': {
        const run = this.run(cmd.task_id);
        for (const other of this.runs) {
          if (other !== run && other.state === 'ACTIVE') this.taskEvent(other, 'pause', now); // auto-pause (§7.4.2)
        }
        if (run.state === 'PAUSED' || run.state === 'BLOCKED') return this.handle({ type: 'TASK_RESUME', task_id: run.task.task_id });
        nextTaskState(run.state, 'start');
        const { estimate, context } = this.estimateFor(run, now);
        run.startEstimate = estimate;
        run.progressStart = { units: Number(this.store.value('progress_units') ?? 0), cycles: Number(this.store.value('load_cycles') ?? 0) };
        this.append({ kind: 'inference', subtype: 'estimate', source: 'inferred', observed_at: now, confidence: 'medium',
          rule_or_model_version: `estimate@1;profile=${this.profile.profile_id}@${this.profile.version}`,
          payload: { task_id: run.task.task_id, basis: estimate.basis, baseline_min: estimate.baseline_min,
            p10_min: estimate.p10_min, p50_min: estimate.p50_min, p90_min: estimate.p90_min,
            expected_wait_min: expectedWaitMin(this.profile, run.task.task_type, this.recentWaits(run.task.task_type)),
            factors: estimate.factors, artifact_id: estimate.artifact_id, personal_offset: null,
            context: { weather: context.weather, visibility: context.visibility, temperature_band: context.temperature_band,
              time_of_day: context.time_of_day, site_congestion: context.site_congestion, darkness: context.darkness } } });
        this.taskEvent(run, 'start', now);
        return { ok: true };
      }
      case 'TASK_PAUSE':
        this.taskEvent(this.run(cmd.task_id), 'pause', now);
        return { ok: true };
      case 'TASK_RESUME': {
        const run = this.run(cmd.task_id);
        for (const other of this.runs) if (other !== run && other.state === 'ACTIVE') this.taskEvent(other, 'pause', now);
        if (!run.startEstimate) {
          // A task that arrived blocked from the previous shift resumes as a start
          run.state = 'PLANNED';
          run.blocker = null;
          return this.handle({ type: 'TASK_START', task_id: run.task.task_id });
        }
        this.taskEvent(run, 'resume', now);
        run.blocker = null;
        return { ok: true };
      }
      case 'TASK_BLOCK': {
        const run = this.run(cmd.task_id);
        const before = run.state === 'ACTIVE' ? this.liveFor(run, now) : null;
        run.blocker = cmd.reason;
        this.taskEvent(run, 'block', now, { reason_code: cmd.reason });
        this.dropPrompt('block_reason');
        if (before) this.computeImpact(run, before.finish50, now);
        return { ok: true };
      }
      case 'TASK_COMPLETE': {
        const run = this.run(cmd.task_id);
        if (!(cmd.output_qty > 0)) return { ok: false, message: 'Output must be more than zero' };
        const acc = timeAccounting(run.intervals, this.idleSpansFor(run.task.task_id), now);
        const start = run.intervals[0]?.start ?? now;
        this.taskEvent(run, 'complete', now, {
          output_qty: cmd.output_qty, actual_start: new Date(start).toISOString(), actual_end: new Date(now).toISOString(),
          active_min: acc.active_min, waiting_min: acc.waiting_min, break_min: acc.break_min, paused_min: acc.paused_min,
        });
        this.dropPrompt('complete_output');
        if (this.impact?.current_task_id === run.task.task_id) this.impact = null;
        return { ok: true };
      }
      case 'TASK_REQUEST_REASSIGN':
      case 'TASK_NOTIFY_SUPERVISOR': {
        const run = this.run(cmd.task_id);
        const kind = cmd.type === 'TASK_REQUEST_REASSIGN' ? 'reassignment' : 'supervisor_notification';
        if (run.pendingRequest === kind) return { ok: false, message: 'Already sent' };
        const impact = this.impact?.current_task_id === run.task.task_id ? this.impact : null;
        if (cmd.type === 'TASK_REQUEST_REASSIGN') {
          this.append({ kind: 'report', subtype: 'reassignment_request', source: 'reported', observed_at: now,
            payload: { task_id: run.task.task_id, reason_code: cmd.reason, impact } });
          this.dropPrompt('reassign_reason');
        } else {
          const reason = run.blocker ?? (this.lastReasonEntry ? String(this.lastReasonEntry.payload.reason_code) : 'other');
          this.append({ kind: 'report', subtype: 'supervisor_notification', source: 'reported', observed_at: now,
            payload: { task_id: run.task.task_id, reason_code: reason, source_entry_id: this.lastReasonEntry?.entry_id ?? run.task.task_id,
              impact: impact ?? { current_task_id: run.task.task_id, current_delta_min: 0, current_p50_finish_at: null,
                next_task_id: null, next_planned_start_at: null, next_window_end_at: null, risk: 'unavailable' } } });
        }
        run.pendingRequest = kind;          // order and assignee never change here (F4-R10)
        return { ok: true };
      }
      case 'IDLE_REASON': {
        const active = this.activeRun();
        const before = active && active.state === 'ACTIVE'
          ? (this.finishBeforeDelay ?? this.liveFor(active, now, null)?.finish50 ?? null) : null;
        const ev = this.idle.current;
        const idleId = ev?.idle_event_id ?? this.init.newId();
        const entry = this.append({ kind: 'report', subtype: 'idle_reason', source: 'reported', observed_at: now,
          original_text: cmd.original_text ?? null, payload: { idle_event_id: idleId, reason_code: cmd.reason, free_text: null, via: cmd.via } });
        this.lastReasonEntry = entry;
        if (ev) {
          this.idle.setReason(cmd.reason, entry.entry_id);
          const rec = this.idleRecords.find((r) => r.idle_event_id === ev.idle_event_id);
          if (rec) {
            rec.category = idleCategory(cmd.reason);
            rec.reason_entry_id = entry.entry_id;
          } else {
            this.idleRecords.push({ idle_event_id: ev.idle_event_id, start: ev.t0, end: null, reason_entry_id: entry.entry_id,
              category: idleCategory(cmd.reason), task_id: ev.task_id });
          }
        }
        this.dropPrompt('idle_reason');
        this.alerts.clear('idle_ask', 'answered', now);
        if (active && before !== null && idleCategory(cmd.reason) === 'site_delay') this.computeImpact(active, before, now);
        return { ok: true };
      }
      case 'CORRECT_LAST_REASON': {
        const target = this.lastReasonEntry;
        if (!target) return { ok: false, message: 'No recent report to change' };
        const payload = { ...(target.payload as Record<string, unknown>), reason_code: cmd.reason, via: 'button' };
        const corr = this.append({ kind: 'correction', subtype: 'idle_reason', source: 'reported', observed_at: now,
          supersedes: target.entry_id, payload: { target_kind: 'report', target_subtype: 'idle_reason', replacement: payload } });
        const rec = this.idleRecords.find((r) => r.reason_entry_id === target.entry_id);
        if (rec) rec.category = idleCategory(cmd.reason);
        if (this.idle.current && this.idle.current.reason_entry_id === target.entry_id) this.idle.current.reason = cmd.reason;
        this.lastReasonEntry = { ...target, payload, entry_id: target.entry_id };
        void corr;
        const active = this.activeRun();
        if (active && active.state === 'ACTIVE' && this.impact) this.computeImpact(active, this.lastFinish50, now);
        return { ok: true };
      }
      case 'ALERT_ACK': {
        if (this.safeExit.view.active) {
          this.safeExit.cancel(now);           // ACK on A7E = "Not exiting"
          return { ok: true };
        }
        this.alerts.ack(now);
        return { ok: true };
      }
      case 'SAFE_EXIT_CANCEL':
        this.safeExit.cancel(now);
        return { ok: true };
      case 'OPEN_PROMPT': {
        const run = this.run(cmd.task_id);
        if (cmd.prompt === 'block_reason') {
          this.pushPrompt({ type: 'block_reason', title: `Why is ${run.task.task_type.replace('_', ' ')} blocked?`, dismissible: true,
            expires_at: null, context: { task_id: run.task.task_id },
            options: (['access_blocked', 'utility_mark', 'waiting_instruction', 'weather'] as BlockReason[]).map((k) => ({ key: k, label: BLOCK_LABEL[k] })) });
        } else if (cmd.prompt === 'reassign_reason') {
          this.pushPrompt({ type: 'reassign_reason', title: 'Why request reassignment?', dismissible: true, expires_at: null,
            context: { task_id: run.task.task_id },
            options: (['machine_fault', 'not_trained', 'access_blocked', 'other'] as ReassignReason[]).map((k) => ({ key: k, label: REASSIGN_LABEL[k] })) });
        } else {
          const q = run.task.quantity;
          const unit = run.task.unit;
          const done = Math.round(this.progressOf(run, now) * 10) / 10;
          this.pushPrompt({ type: 'complete_output', title: `Complete ${run.task.task_type.replace('_', ' ')}? Confirm output`, dismissible: true,
            expires_at: null, context: { task_id: run.task.task_id },
            options: [{ key: String(q), label: `${q} ${unit} (planned)` },
              ...(done > 0 && done !== q ? [{ key: String(done), label: `${done} ${unit} (measured)` }] : []),
              { key: String(Math.round(q * 0.5 * 10) / 10), label: `${Math.round(q * 0.5 * 10) / 10} ${unit} (half)` }] });
        }
        return { ok: true };
      }
      case 'PROMPT_ANSWER': {
        const p = this.prompts.find((x) => x.prompt_id === cmd.prompt_id);
        if (!p) return { ok: false, message: 'Prompt closed' };
        const taskId = String(p.context.task_id ?? '');
        this.prompts = this.prompts.filter((x) => x !== p);
        if (p.type === 'idle_reason') return this.handle({ type: 'IDLE_REASON', reason: cmd.option as IdleReason, via: 'button' });
        if (p.type === 'block_reason') return this.handle({ type: 'TASK_BLOCK', task_id: taskId, reason: cmd.option as BlockReason });
        if (p.type === 'reassign_reason') return this.handle({ type: 'TASK_REQUEST_REASSIGN', task_id: taskId, reason: cmd.option as ReassignReason });
        if (p.type === 'complete_output') return this.handle({ type: 'TASK_COMPLETE', task_id: taskId, output_qty: Number(cmd.option) });
        return { ok: true };
      }
      case 'PROMPT_DISMISS': {
        const p = this.prompts.find((x) => x.prompt_id === cmd.prompt_id);
        if (p && p.dismissible) this.prompts = this.prompts.filter((x) => x !== p);
        return { ok: true };
      }
      case 'CONDITION_REPORT':
        this.conditionReports.push({ condition: cmd.condition, active: cmd.active, at: now });
        this.append({ kind: 'report', subtype: 'condition_report', source: 'reported', observed_at: now,
          payload: { condition: cmd.condition, active: cmd.active } });
        return { ok: true };
      case 'DISMISS_IMPACT':
        this.impact = null;
        return { ok: true };
      case 'END_SHIFT':
        if (!this.shift) return { ok: false, message: 'No open shift' };
        this.append({ kind: 'shift_event', subtype: 'end', source: 'reported', observed_at: now, payload: { handover_id: null } });
        this.shift = null;
        return { ok: true };
    }
  }

  private taskEvent(run: TaskRun, event: 'start' | 'pause' | 'resume' | 'block' | 'complete', now: number, extra: Record<string, unknown> = {}): void {
    const next = nextTaskState(run.state, event);
    const open = run.intervals[run.intervals.length - 1];
    if (open && open.end === null) open.end = now;
    if (next === 'ACTIVE' || next === 'PAUSED' || next === 'BLOCKED') run.intervals.push({ state: next, start: now, end: null });
    run.state = next;
    this.append({ kind: 'task_event', subtype: event, source: 'reported', observed_at: now, payload: {
      task_id: run.task.task_id, assignment_revision: run.task.revision, reason_code: null, output_qty: null, actual_start: null,
      actual_end: null, active_min: null, waiting_min: null, break_min: null, paused_min: null, ...extra } });
  }

  private computeImpact(run: TaskRun, finish50Before: number | null, now: number): void {
    const after = run.state === 'ACTIVE' ? this.liveFor(run, now) : this.liveFor({ ...run, state: 'ACTIVE' }, now);
    const next = nextPlannedTask(this.runs.map((r) => ({ task: r.task, state: r.state })), run.task);
    this.impact = impactPreview({ currentTaskId: run.task.task_id, finish50Before, finish50After: after?.finish50 ?? null,
      finish90After: after?.finish90 ?? null, next });
  }

  // ---------------------------------------------------------------------------------------------- tick

  /** One simulated second (§8.16.3). */
  tick(sample: SignalSample, detections: DetectionEvent[], heartbeat: ProximityHeartbeat | null): void {
    const now = sample.ts;
    this.lastTickTs = now;
    // 1. ingest
    this.store.ingest(sample);
    this.proximity.ingest(detections, heartbeat);
    // 2. machine state
    const change = this.sm.evaluate(this.store, now);
    if (change) {
      this.append({ kind: 'inference', subtype: 'machine_state_change', source: 'inferred', observed_at: now, confidence: 'high',
        rule_or_model_version: `machine_state@1;profile=${this.profile.profile_id}@${this.profile.version}`,
        payload: { from: change.from, to: change.to, reason: change.reason } });
    }
    const state = this.sm.state;
    // 3. safety rules
    const cond = this.conditions(now);
    this.seatbelt.evaluate(this.store, state, now);
    this.safeExit.evaluate(this.store, state, now);
    this.proximity.evaluate(this.store, cond.multiplier, now);
    this.speed.evaluate(this.store, now);
    // 4. idle tracker
    const active = this.runs.find((r) => r.state === 'ACTIVE') ?? null;
    for (const sig of this.idle.tick(this.store, state, now, active?.task.task_id ?? null)) this.onIdle(sig, now);
    // 6. alert-budget operating time
    if (this.store.bool('engine_on', now) === true) this.alerts.countOperatingSecond(now);
    // 9. prompt expiry
    this.prompts = this.prompts.filter((p) => p.expires_at === null || p.expires_at > now);
    // 10. repeats
    this.alerts.tickRepeats(now);
    const live = active ? this.liveFor(active, now) : null;
    if (live) {
      this.lastFinish50 = live.finish50;
      if (!this.idle.current) this.finishBeforeDelay = live.finish50;   // frozen while an idle/delay is in progress
    }
  }

  private onIdle(sig: ReturnType<IdleTracker['tick']>[number], now: number): void {
    const rule = `idle@1;profile=${this.profile.profile_id}@${this.profile.version}`;
    if (sig.type === 'recorded') {
      const ev = sig.event;
      this.append({ kind: 'idle_event', subtype: 'started', source: 'observed', observed_at: now,
        payload: { idle_event_id: ev.idle_event_id, candidate_started_at: new Date(ev.t0).toISOString(), task_id: ev.task_id, zone_id: null } });
      if (!this.idleRecords.some((r) => r.idle_event_id === ev.idle_event_id)) {
        this.idleRecords.push({ idle_event_id: ev.idle_event_id, start: ev.t0, end: null, reason_entry_id: ev.reason_entry_id,
          category: ev.reason ? idleCategory(ev.reason) : null, task_id: ev.task_id });
      }
    } else if (sig.type === 'prompt') {
      const order = this.profile.idle.default_reason_order;
      this.alerts.raise('A-IDLE-ASK', 'INFO', 'idle_ask', {}, now);
      this.pushPrompt({ type: 'idle_reason', title: 'Why the wait?', dismissible: true,
        expires_at: now + this.profile.idle.prompt_timeout_s * 1000, context: { idle_event_id: sig.event.idle_event_id },
        options: order.slice(0, 4).map((k) => ({ key: k, label: REASON_LABEL[k] })) });
    } else if (sig.type === 'prompt_expired') {
      this.dropPrompt('idle_reason');
      this.alerts.clear('idle_ask', 'unanswered', now);
    } else if (sig.type === 'ended') {
      const { event: ev, duration_s, idle_class, category, non_required_s } = sig.ended;
      this.append({ kind: 'idle_event', subtype: 'ended', source: 'observed', observed_at: now,
        payload: { idle_event_id: ev.idle_event_id, ended_at: new Date(now).toISOString(), duration_s, required_s: ev.required_s } });
      this.append({ kind: 'inference', subtype: 'idle_classification', source: 'inferred', observed_at: now, confidence: 'high',
        rule_or_model_version: rule, payload: { idle_event_id: ev.idle_event_id, idle_class, required_s: ev.required_s,
          non_required_s, category } });
      const rec = this.idleRecords.find((r) => r.idle_event_id === ev.idle_event_id);
      if (rec) rec.end = now;
      this.dropPrompt('idle_reason');
      this.alerts.clear('idle_ask', 'idle_ended', now);
    }
  }

  // ---------------------------------------------------------------------------------------------- snapshot

  snapshot(): EngineSnapshot {
    const now = this.now();
    const state = this.sm.state;
    const cond = this.conditions(now);
    const operating = state === 'WORKING' || state === 'TRAVELLING' || state === 'UNKNOWN';

    // Prompt deferral: while operating, non-critical prompts wait until READY/SECURED (§8.16.4, NFR-17)
    let prompt: Prompt | null = null;
    for (const p of this.prompts) {
      if (operating) {
        if (!p.deferred_counted) {
          p.deferred_counted = true;
          this.alerts.countDeferredPrompt(now);
        }
        continue;
      }
      prompt = p;
      break;
    }

    const views = this.taskViews(now);
    const active = views.find((v) => v.state === 'ACTIVE') ?? null;
    let dayFinish: EngineSnapshot['day_finish'] = null;
    if (views.length) {
      let p50 = now;
      let p90 = now;
      for (const v of views) {
        if (v.state === 'COMPLETED' || v.state === 'CANCELLED') continue;
        if (v.live) {
          p50 = Math.max(p50, v.live.finish50);
          p90 = Math.max(p90, v.live.finish90);
        } else if (v.estimate.p50_min !== null && v.estimate.p90_min !== null && v.state !== 'BLOCKED') {
          p50 += (v.estimate.p50_min + v.expected_wait_min) * MINUTE;
          p90 += (v.estimate.p90_min + v.expected_wait_min) * MINUTE;
        }
      }
      dayFinish = { p50_at: p50, p90_at: p90 };
    }

    const idle = this.idle.current;
    const top = this.alerts.active()[0] ?? null;
    const health: SignalName[] = ['engine_on', 'ground_speed_kmh', this.profile.secure_signal, 'seatbelt_fastened', 'seat_occupied',
      'cab_door_open', 'implement_neutral', 'load_factor_pct'];
    return {
      now,
      local_time: formatHHMM(now, this.init.site.utc_offset_minutes),
      site: this.init.site,
      machine: { ...this.init.machine, state, state_since: this.sm.stateSince, display_name: this.profile.display_name },
      shift: this.shift,
      signal_health: health.map((name) => ({ name, fresh: this.store.fresh(name, now), age_ms: this.store.age(name, now) })),
      conditions: cond,
      alerts: { active: this.alerts.active(), top, budget: this.alerts.budget },
      safe_exit: this.safeExit.view,
      belt: this.seatbelt.pill,
      proximity: this.proximity.pill,
      speed: { speed_kmh: this.speed.speed, limit_kmh: this.profile.speed ? this.speed.limit : null,
        over: this.speed.speed !== null && this.speed.limit !== null && !!this.profile.speed && this.speed.speed > this.speed.limit },
      prompt,
      prompts_waiting: this.prompts.length - (prompt ? 1 : 0),
      tasks: views,
      active_task_id: active?.task.task_id ?? null,
      day_finish: dayFinish,
      impact: this.impact,
      idle: idle ? { ...idle, non_required_s: idle.elapsed_s - idle.required_s } : null,
      briefing: this.briefing(now, cond, views),
      ledger_count: this.ledger.all().length,
      pending_sync: this.ledger.all().filter((e) => e.sync_status === 'pending' && e.audience !== 'operator_only').length,
      pin_lockout_until: Object.fromEntries(Object.entries(this.lockouts).filter(([, s]) => s.locked_until && s.locked_until > now)
        .map(([k, s]) => [k, s.locked_until as number])),
      illustrative_notice: this.profile.illustrative_notice,
    };
  }

  private taskViews(now: number): TaskView[] {
    const nextId = this.runs.find((r) => r.state === 'PLANNED')?.task.task_id ?? null;
    const done = new Map<string, number>();
    for (const e of [...this.init.history, ...this.ledger.all()]) {
      if (e.kind === 'task_event' && e.subtype === 'complete' && e.operator_id === this.shift?.operator.operator_id) {
        const t = this.runs.find((r) => r.task.task_id === e.payload.task_id)?.task.task_type;
        if (t) done.set(t, (done.get(t) ?? 0) + 1);
      }
    }
    return this.runs.map((run) => {
      const estimate = run.startEstimate ?? this.estimateFor(run, now).estimate;
      const zone = this.init.zones.find((z) => z.zone_id === run.task.zone_id);
      const started = run.intervals.length > 0;
      return {
        task: run.task,
        state: run.state,
        is_next: run.task.task_id === nextId,
        estimate,
        expected_wait_min: expectedWaitMin(this.profile, run.task.task_type, this.recentWaits(run.task.task_type)),
        live: started && run.state !== 'COMPLETED' ? this.liveFor(run, now) : null,
        accounting: started ? timeAccounting(run.intervals, this.idleSpansFor(run.task.task_id), now) : null,
        progress: Math.round(this.progressOf(run, now) * 10) / 10,
        blocker: run.blocker,
        pending_request: run.pendingRequest,
        unfamiliar: (done.get(run.task.task_type) ?? 0) < 3,
        zone_name: zone?.name ?? null,
      };
    });
  }

  private briefing(now: number, cond: EffectiveConditions, views: TaskView[]): BriefingView {
    const items = this.init.handoverItems.filter((i) => i.status === 'open').map((i) => ({ ...i, acknowledged: this.acked.has(i.item_id) }));
    const notes: string[] = [];
    const defect = items.find((i) => i.item_type === 'defect');
    if (defect) notes.push(`Last shift: ${defect.text.split(' — ')[0]}. Check before starting.`);
    const blocked = views.find((v) => v.state === 'BLOCKED');
    if (blocked) notes.push(`${blocked.task.task_type.replace('_', ' ')} at ${blocked.zone_name ?? 'site'} is blocked: ${BLOCK_LABEL[blocked.blocker ?? 'other'].toLowerCase()}. Check with the supervisor.`);
    const rainHour = cond.rain ? now : this.init.forecast.find((h) => h.valid_from >= now && h.valid_from <= now + 10 * HOUR && (h.weather === 'rain' || h.precipitation_mm >= 0.5))?.valid_from;
    if (rainHour !== undefined && notes.length < 3) {
      const when = cond.rain ? 'now' : `after ${formatHHMM(rainHour, this.init.site.utc_offset_minutes)}`;
      const where = this.profile.machine_class === 'haul_truck' ? 'haul roads may be slippery' : 'trenches may be slippery';
      notes.push(`Rain ${when}: ${where}; proximity warnings will start earlier.`);
    }
    if (cond.dust && notes.length < 3) notes.push('Dust: low visibility; proximity warnings will start earlier.');
    if (cond.darkness && notes.length < 3) notes.push('Working after dark: proximity warnings will start earlier.');
    const hour = forecastAt(this.init.forecast, now);
    const old = !!hour && now - hour.issued_at > 6 * HOUR;
    const ageH = hour ? Math.round((now - hour.issued_at) / HOUR) : null;
    const conditionsText = hour
      ? `${cond.rain ? 'Rain' : cond.dust ? 'Dust' : hour.weather === 'clear' ? 'Clear' : hour.weather} · ${Math.round(hour.temp_c)} °C · Forecast ${ageH} h old`
      : 'Conditions unknown — press 3 to report';
    return { handover: items, all_acknowledged: items.every((i) => i.acknowledged), risk_notes: notes.slice(0, 3),
      conditions_text: conditionsText, conditions_old: old, task_count: views.length };
  }

  /** A1 roster: operators with a shift on this machine in the history first, then A–Z (no PIN material). */
  roster(): { operator_id: string; display_name: string; skill_level: string; language: string }[] {
    const recent = new Set(this.init.history.map((e) => e.operator_id).filter((x): x is string => !!x));
    return [...this.init.operators]
      .sort((a, b) => Number(recent.has(b.operator_id)) - Number(recent.has(a.operator_id)) || a.display_name.localeCompare(b.display_name))
      .map((o) => ({ operator_id: o.operator_id, display_name: o.display_name, skill_level: o.skill_level, language: o.language }));
  }

  /** Speech produced since the last call (app speaks it; clips/TTS per F11-R4). */
  drainSpeech(): SpeechOut[] {
    return this.alerts.drainSpeech();
  }

  get lastTick(): number | null {
    return this.lastTickTs;
  }

  zoneAt(lat: number, lon: number): Zone | null {
    return zoneAt(lat, lon, this.init.zones);
  }

  static hashPin = hashPin;
}
