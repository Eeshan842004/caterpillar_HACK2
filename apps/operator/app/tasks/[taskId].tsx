// A4 Task detail (F4-R1, R6, R7): active range, expected waiting, finish range, basis, model contributions
// (labelled as such, not causes), planner comparison, progress and time accounting.
import { useLocalSearchParams, useRouter } from 'expo-router';
import { View } from 'react-native';
import { host, useHost } from '../../src/engine/host';
import { Row, Screen, Section, StatusPill, T } from '../../src/ui/components';
import { STATE_TONE, basisText, clock, mins, taskLabel } from '../../src/ui/format';
import { useFocusList } from '../../src/ui/useFocusList';
import { space } from '../../src/ui/tokens';

export default function TaskDetail() {
  const router = useRouter();
  const { taskId } = useLocalSearchParams<{ taskId: string }>();
  const snap = useHost((s) => s.snapshot);
  const v = snap?.tasks.find((t) => t.task.task_id === taskId);
  useFocusList(1, () => undefined, (k) => {
    if (!v) return false;
    const id = v.task.task_id;
    if (k.action === 'BACK') router.replace('/tasks');
    else if (k.action === 'QUICK_1') host.dispatch({ type: v.state === 'PAUSED' || v.state === 'BLOCKED' ? 'TASK_RESUME' : 'TASK_START', task_id: id });
    else if (k.action === 'QUICK_2') host.dispatch({ type: 'TASK_PAUSE', task_id: id });
    else if (k.action === 'QUICK_3') host.dispatch({ type: 'OPEN_PROMPT', prompt: 'block_reason', task_id: id });
    else if (k.action === 'QUICK_4') host.dispatch({ type: 'OPEN_PROMPT', prompt: 'complete_output', task_id: id });
    else return false;
    return true;
  });
  if (!snap || !v) return <Screen title="Task not found" hints="Back returns to tasks"><T muted>This task is no longer on the board.</T></Screen>;
  const e = v.estimate;
  const offset = snap.site.utc_offset_minutes;
  const startAt = v.task.planned_start_at && v.task.planned_start_at > snap.now ? v.task.planned_start_at : snap.now;
  const finish = (m: number | null) => (m === null ? '—' : clock(startAt + (m + v.expected_wait_min) * 60_000, offset));
  return (
    <Screen title={`${taskLabel(v.task.task_type)} · ${v.task.quantity} ${v.task.unit} ${v.task.material}`}
      hints="1 start/resume · 2 pause · 3 block · 4 complete · Back tasks">
      <View style={{ flexDirection: 'row', gap: space.md, alignItems: 'center' }}>
        <StatusPill tone={STATE_TONE[v.state]} word={v.state} />
        <T muted>{v.zone_name ?? v.task.location_text} · {v.task.completion_criterion}</T>
      </View>
      {snap.shift?.guidance === 'guided' && v.unfamiliar && v.state === 'PLANNED' ? (
        <StatusPill tone="info" word="New task type for you" detail="Guided preparation card arrives with the content pack (T30)" />
      ) : null}
      <Section title="Estimate">
        {e.basis === 'insufficient_data' ? <T>Insufficient data — no rate for this task and material.</T> : (
          <>
            <T variant="heading">{mins(e.p10_min)}–{mins(e.p90_min)} min active · ~{v.expected_wait_min} min waiting · finish {finish(e.p10_min)}–{finish(e.p90_min)}</T>
            <T>Basis: {basisText(e.basis)} · baseline {mins(e.baseline_min)} min{v.task.planner_minutes !== null ? ` · planner ${v.task.planner_minutes} min` : ''}</T>
            {e.factors.length
              ? <T>{e.factors.map((f) => `${f.factor} ${f.pct >= 0 ? '+' : ''}${f.pct}%`).join(' · ')} (model contributions, not proven causes)</T>
              : <T muted>No learned factors yet: the trained estimator (T36) is not installed, so the range is the baseline fallback band.</T>}
          </>
        )}
      </Section>
      {v.live ? (
        <Section title="Live">
          <T variant="heading">{v.progress} / {v.task.quantity} {v.task.unit} · {v.live.progressPct}%</T>
          <T>{v.live.mode === 'conditional' ? `About ${mins(v.live.rem50)} min after work resumes`
            : `Finish ${clock(v.live.finish10, offset)}–${clock(v.live.finish90, offset)} (P50 ${clock(v.live.finish50, offset)})`}</T>
          {v.accounting ? <T muted>Active {v.accounting.active_min} · waiting {v.accounting.waiting_min} · break {v.accounting.break_min} · paused {v.accounting.paused_min} min</T> : null}
        </Section>
      ) : null}
      <Row focused onPress={() => router.replace('/tasks')}>
        <T variant="heading">Back to tasks</T>
      </Row>
      <T variant="caption" muted>{snap.illustrative_notice} Estimates come from simulated training data.</T>
    </Screen>
  );
}
