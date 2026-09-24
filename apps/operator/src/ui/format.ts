// Display helpers: whole minutes, site-local clock times, task labels.
import { formatHHMM, type TaskView } from '@shiftmate/core';

export const taskLabel = (t: string) => t.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());

export function mins(v: number | null | undefined): string {
  return v === null || v === undefined ? '—' : `${Math.round(v)}`;
}

export function clock(ts: number | null | undefined, offset: number): string {
  return ts === null || ts === undefined ? '—' : formatHHMM(ts, offset);
}

export function rangeText(v: TaskView): string {
  const e = v.estimate;
  if (e.p10_min === null || e.p90_min === null) return 'Insufficient data';
  return `${mins(e.p10_min)}–${mins(e.p90_min)} min active`;
}

export function basisText(b: string): string {
  return b === 'comparable_history' ? 'Comparable history' : b === 'fallback' ? 'Fallback baseline only' : 'Insufficient data';
}

export const STATE_TONE = {
  PLANNED: 'info', ACTIVE: 'ok', PAUSED: 'caution', BLOCKED: 'warning', COMPLETED: 'ok', CANCELLED: 'unavailable',
} as const;
