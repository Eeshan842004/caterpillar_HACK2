// Task model (§7.4.2), time accounting (§8.6.7), day plan and downstream impact preview (§8.6.9).
import type { BlockReason, IdleCategory, ImpactRisk, TaskAssignment, TaskState } from '../types';

export type TaskEventName = 'start' | 'pause' | 'resume' | 'block' | 'complete' | 'cancel';

export interface Interval {
  state: 'ACTIVE' | 'PAUSED' | 'BLOCKED';
  start: number;
  end: number | null;
}

export interface IdleSpan {
  start: number;
  end: number | null;
  category: IdleCategory | null; // effective (after corrections); null = unexplained / required → stays active
}

export class TaskTransitionError extends Error {}

/** Legal transitions (§7.4.2). Returns the next state or throws with the spoken reason. */
export function nextTaskState(current: TaskState, event: TaskEventName): TaskState {
  if (current === 'COMPLETED' || current === 'CANCELLED') throw new TaskTransitionError('Task already finished');
  switch (event) {
    case 'start':
      if (current !== 'PLANNED') throw new TaskTransitionError('Task already started');
      return 'ACTIVE';
    case 'pause':
      if (current !== 'ACTIVE') throw new TaskTransitionError('Only an active task can be paused');
      return 'PAUSED';
    case 'block':
      if (current !== 'PLANNED' && current !== 'ACTIVE') throw new TaskTransitionError('Task cannot be blocked now');
      return 'BLOCKED';
    case 'resume':
      if (current !== 'PAUSED' && current !== 'BLOCKED') throw new TaskTransitionError('Task is not paused or blocked');
      return 'ACTIVE';
    case 'complete':
      if (current === 'BLOCKED') throw new TaskTransitionError('Resume the task first');
      if (current !== 'ACTIVE' && current !== 'PAUSED') throw new TaskTransitionError('Start the task first');
      return 'COMPLETED';
    case 'cancel':
      return 'CANCELLED';
  }
}

function overlapMs(aStart: number, aEnd: number, bStart: number, bEnd: number): number {
  return Math.max(0, Math.min(aEnd, bEnd) - Math.max(aStart, bStart));
}

export interface Accounting {
  active_min: number;
  waiting_min: number;
  break_min: number;
  paused_min: number;
}

/**
 * §8.6.7: within ACTIVE intervals, overlap with site_delay/other idle → waiting, with break idle → break,
 * unexplained/required idle stays active; BLOCKED → waiting; PAUSED → paused.
 */
export function timeAccounting(intervals: Interval[], idles: IdleSpan[], now: number): Accounting {
  let active = 0;
  let waiting = 0;
  let brk = 0;
  let paused = 0;
  for (const iv of intervals) {
    const end = iv.end ?? now;
    const len = Math.max(0, end - iv.start);
    if (iv.state === 'PAUSED') paused += len;
    else if (iv.state === 'BLOCKED') waiting += len;
    else {
      let w = 0;
      let b = 0;
      for (const idle of idles) {
        const ov = overlapMs(iv.start, end, idle.start, idle.end ?? now);
        if (idle.category === 'site_delay' || idle.category === 'other') w += ov;
        else if (idle.category === 'break') b += ov;
      }
      waiting += w;
      brk += b;
      active += len - w - b;
    }
  }
  const m = (ms: number) => Math.round((ms / 60_000) * 10) / 10;
  return { active_min: m(active), waiting_min: m(waiting), break_min: m(brk), paused_min: m(paused) };
}

export interface ImpactSummary {
  current_task_id: string;
  current_delta_min: number;
  current_p50_finish_at: number | null;
  next_task_id: string | null;
  next_planned_start_at: number | null;
  next_window_end_at: number | null;
  risk: ImpactRisk;
}

/** §8.6.9: compare the current task's finish with the next task's planned start window. Never mutates tasks. */
export function impactPreview(args: {
  currentTaskId: string;
  finish50Before: number | null;
  finish50After: number | null;
  finish90After: number | null;
  next: TaskAssignment | null;
}): ImpactSummary {
  const { next } = args;
  const delta = args.finish50Before !== null && args.finish50After !== null
    ? Math.round((args.finish50After - args.finish50Before) / 60_000) : 0;
  const base = {
    current_task_id: args.currentTaskId, current_delta_min: delta, current_p50_finish_at: args.finish50After,
    next_task_id: next?.task_id ?? null, next_planned_start_at: next?.planned_start_at ?? null,
  };
  if (args.finish50After === null || args.finish90After === null || !next || next.planned_start_at === null) {
    return { ...base, next_window_end_at: null, risk: 'unavailable' };
  }
  const windowEnd = next.planned_start_at + next.planned_start_window_min * 60_000;
  const risk: ImpactRisk = args.finish50After > windowEnd ? 'likely_miss' : args.finish90After > windowEnd ? 'at_risk' : 'none';
  return { ...base, next_window_end_at: windowEnd, risk };
}

/** Next PLANNED task by immutable sequence after the given one (same machine and date). */
export function nextPlannedTask(tasks: { task: TaskAssignment; state: TaskState }[], after: TaskAssignment): TaskAssignment | null {
  return tasks
    .filter((t) => t.state === 'PLANNED' && t.task.sequence > after.sequence && t.task.planned_date === after.planned_date)
    .sort((a, b) => a.task.sequence - b.task.sequence)[0]?.task ?? null;
}

export type { BlockReason };
