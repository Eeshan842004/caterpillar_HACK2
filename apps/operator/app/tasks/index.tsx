// A3 Task board (F3, F4-R9…R11): every task field, next task highlighted, day finish, the downstream impact card
// after an accepted delay (order never changes), pending request badges, "change last report" (CORRECT_LAST).
import { LABELS, type IdleReason } from '@shiftmate/core';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';
import { host, useHost } from '../../src/engine/host';
import { useKeys } from '../../src/input/keys';
import { Row, Screen, StatusPill, T } from '../../src/ui/components';
import { STATE_TONE, basisText, clock, mins, rangeText, taskLabel } from '../../src/ui/format';
import { useFocusList } from '../../src/ui/useFocusList';
import { space } from '../../src/ui/tokens';

const RISK_TEXT = {
  likely_miss: 'may miss its planned start window', at_risk: 'is at risk of missing its planned start window',
  none: 'should still start on time', unavailable: '',
} as const;

export default function TaskBoard() {
  const router = useRouter();
  const snap = useHost((s) => s.snapshot);
  const [changing, setChanging] = useState(false);
  const tasks = snap?.tasks ?? [];
  const impact = snap?.impact ?? null;
  const rows: ('impact' | 'change' | number)[] = [...(impact ? ['impact' as const] : []), ...tasks.map((_, i) => i), 'change'];

  const act = (row: (typeof rows)[number] | undefined, key: 'OK' | 1 | 2 | 3 | 4) => {
    if (row === undefined) return;
    if (row === 'impact' && impact) {
      if (key === 1) host.dispatch({ type: 'OPEN_PROMPT', prompt: 'reassign_reason', task_id: impact.current_task_id });
      if (key === 2) host.dispatch({ type: 'TASK_NOTIFY_SUPERVISOR', task_id: impact.current_task_id });
      if (key === 'OK') host.dispatch({ type: 'DISMISS_IMPACT' });
      return;
    }
    if (row === 'change') {
      if (key === 'OK') setChanging(true);
      return;
    }
    if (typeof row !== 'number') return;
    const v = tasks[row];
    if (!v) return;
    const id = v.task.task_id;
    if (key === 'OK') router.push(`/tasks/${id}` as never);
    if (key === 1) host.dispatch({ type: v.state === 'PAUSED' || v.state === 'BLOCKED' ? 'TASK_RESUME' : 'TASK_START', task_id: id });
    if (key === 2) host.dispatch({ type: 'TASK_PAUSE', task_id: id });
    if (key === 3) host.dispatch({ type: 'OPEN_PROMPT', prompt: 'block_reason', task_id: id });
    if (key === 4) host.dispatch({ type: 'OPEN_PROMPT', prompt: 'complete_output', task_id: id });
  };

  const [focus] = useFocusList(rows.length, (i) => act(rows[i], 'OK'), (k, i) => {
    if (changing) return false;
    const n = k.action?.startsWith('QUICK_') ? (Number(k.action.slice(6)) as 1 | 2 | 3 | 4) : null;
    if (n === null) return false;
    act(rows[i], n);
    return true;
  });

  // Correction prompt: "Actually, access blocked" by keys (CORRECT_LAST button path, §7.3)
  const reasons: IdleReason[] = snap?.machine.machine_class === 'haul_truck'
    ? ['shovel_queue', 'crusher_queue', 'access_blocked', 'break'] : ['waiting_truck', 'access_blocked', 'instructed_hold', 'break'];
  useKeys((k) => {
    const n = k.action?.startsWith('QUICK_') ? Number(k.action.slice(6)) : null;
    if (n !== null) {
      const r = reasons[n - 1];
      if (r) host.dispatch({ type: 'CORRECT_LAST_REASON', reason: r });
      setChanging(false);
    } else if (k.action === 'BACK') setChanging(false);
    return true;
  }, 140, changing);

  if (!snap) return null;
  const offset = snap.site.utc_offset_minutes;
  const next = impact?.next_task_id ? tasks.find((t) => t.task.task_id === impact.next_task_id) : null;
  let rowIndex = 0;
  return (
    <Screen title="Today's tasks"
      hints={changing ? 'Change last report: 1–4 choose reason · Back cancel'
        : 'OK details · 1 start/resume · 2 pause · 3 block · 4 complete · M menu'}>
      <T muted>
        Next: {tasks.find((t) => t.is_next)?.task.task_type.replace('_', ' ') ?? 'all tasks done'}
        {snap.day_finish ? ` · Day finish ~${clock(snap.day_finish.p50_at, offset)} (late case ${clock(snap.day_finish.p90_at, offset)})` : ''}
      </T>
      {impact ? (
        <Row focused={focus === rowIndex++} onPress={() => host.dispatch({ type: 'DISMISS_IMPACT' })}>
          <T variant="heading">Current task ETA updated by {impact.current_delta_min >= 0 ? '+' : ''}{impact.current_delta_min} minutes</T>
          {impact.risk === 'unavailable'
            ? <T>Downstream impact unavailable (no next task or no planned start window)</T>
            : <T>Task {next?.task.sequence ?? ''} ({taskLabel(next?.task.task_type ?? '')}, window {clock(impact.next_planned_start_at, offset)}–{clock(impact.next_window_end_at, offset)}) {RISK_TEXT[impact.risk]}.</T>}
          <T variant="caption" muted>1 Request reassignment · 2 Notify supervisor · OK dismiss — requests only; order and assignee stay the same</T>
        </Row>
      ) : null}
      {tasks.map((v) => {
        const i = rowIndex++;
        const e = v.estimate;
        return (
          <Row key={v.task.task_id} focused={focus === i} onPress={() => router.push(`/tasks/${v.task.task_id}` as never)}>
            <View style={{ flexDirection: 'row', gap: space.md, alignItems: 'center', flexWrap: 'wrap' }}>
              <T variant="heading">{v.task.sequence}. {taskLabel(v.task.task_type)} {v.task.quantity} {v.task.unit} {v.task.material}</T>
              <StatusPill tone={STATE_TONE[v.state]} word={v.state} detail={v.blocker ? LABELS.BLOCK_LABEL[v.blocker] : undefined} />
              {v.is_next ? <StatusPill tone="info" word="Next" /> : null}
              {v.pending_request ? <StatusPill tone="caution" word="Pending supervisor" detail={v.pending_request.replace('_', ' ')} /> : null}
            </View>
            <T muted>
              {v.zone_name ?? v.task.location_text} · priority {v.task.priority} · done = {v.task.completion_criterion}
            </T>
            <T>
              {v.live ? `${v.live.progressPct}% · finish ${v.live.mode === 'conditional' ? `about ${mins(v.live.rem50)} min after work resumes` : `${clock(v.live.finish10, offset)}–${clock(v.live.finish90, offset)}`}`
                : `${rangeText(v)} · ~${v.expected_wait_min} min waiting`}
              {' · '}Planner {v.task.planner_minutes ?? '—'} min · {basisText(e.basis)}
              {v.task.planned_start_at ? ` · planned ${clock(v.task.planned_start_at, offset)}` : ''}
              {' · '}{v.task.source} rev {v.task.revision}
            </T>
          </Row>
        );
      })}
      <Row focused={focus === rowIndex} onPress={() => setChanging(true)}>
        <T variant="heading">Recent reports — change</T>
        <T variant="caption" muted>Correct the last wait reason; the original stays in history (F9-R6)</T>
      </Row>
    </Screen>
  );
}
