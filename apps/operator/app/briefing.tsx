// A2 Briefing (F2-R1…R5): open handover items (acknowledged ≠ resolved), today, conditions with age, machine
// notes, up to 3 risk notes. Guided mode reads the handover aloud; "Continue" is disabled until all are acknowledged.
import { useRouter } from 'expo-router';
import { useEffect, useRef } from 'react';
import { View } from 'react-native';
import { host, useHost } from '../src/engine/host';
import { ContinuityRail, Row, Screen, Section, StateFlag, T, WorkSurface } from '../src/ui/components';
import { useFocusList } from '../src/ui/useFocusList';
import { speak } from '../src/voice/speaker';
import { clock } from '../src/ui/format';
import { space } from '../src/ui/tokens';

const ITEM_WORD = { blocked_task: 'Blocked task', defect: 'Defect', unfinished_task: 'Unfinished task', incident: 'Incident',
  site_delay: 'Site delay', note: 'Note', tip: 'Tip' } as const;

export default function Briefing() {
  const router = useRouter();
  const snap = useHost((s) => s.snapshot);
  const read = useRef(false);
  const items = snap?.briefing.handover ?? [];
  const allAck = snap?.briefing.all_acknowledged ?? true;
  const readAloud = () => {
    if (!items.length) speak('No open items from last shift.', 4);
    items.forEach((i) => speak(`${ITEM_WORD[i.item_type]}. ${i.text}`, 4));
  };
  useEffect(() => {
    if (!read.current && snap?.shift?.guidance === 'guided') {
      read.current = true;
      readAloud();
    }
  }, [snap?.shift?.guidance]);

  const rows = items.length + 1;
  const [focus] = useFocusList(rows, (i) => {
    const item = items[i];
    if (item) host.dispatch({ type: 'ACK_HANDOVER', item_id: item.item_id });
    else if (allAck) router.replace('/tasks');
    else useHost.setState({ lastMessage: 'Acknowledge every handover item first' });
  }, (k) => {
    if (k.action === 'QUICK_1') readAloud();
    else if (k.action === 'QUICK_2') host.dispatch({ type: 'ACK_HANDOVER', item_id: 'all' });
    else if (k.action === 'QUICK_3') host.dispatch({ type: 'CONDITION_REPORT', condition: 'rain', active: !snap?.conditions.rain });
    else return false;
    return true;
  });
  if (!snap) return null;
  const next = snap.tasks.find((t) => t.is_next);
  const offset = snap.site.utc_offset_minutes;
  return (
    <Screen title={`Briefing for ${snap.shift?.operator.display_name ?? 'operator'}`}
      hints="OK acknowledge · 1 read aloud · 2 acknowledge all · 3 report rain · last row: continue">
      <WorkSurface split>
      <ContinuityRail stops={[{ label: 'Previous shift', detail: `${items.length} open item${items.length === 1 ? '' : 's'}` }, { label: 'Acknowledged context', detail: allAck ? 'Ready for today' : 'Review required' }, { label: 'Today', detail: `${snap.briefing.task_count} tasks` }]} active={allAck ? 2 : 0} />
      <View style={{ flex: 1 }}>
      <Section title="Handover from last shift">
        {items.length === 0 ? <T muted>No open items from last shift.</T> : null}
        <View style={{ gap: space.sm }}>
          {items.map((i, idx) => (
            <Row key={i.item_id} focused={focus === idx} onPress={() => host.dispatch({ type: 'ACK_HANDOVER', item_id: i.item_id })}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.md, flexWrap: 'wrap' }}>
                <StateFlag tone={i.item_type === 'defect' ? 'warning' : 'caution'} word={ITEM_WORD[i.item_type]} />
                <T variant="heading" style={{ flex: 1 }}>{i.text}</T>
                <StateFlag tone={i.acknowledged ? 'ok' : 'info'} word={i.acknowledged ? 'Acknowledged' : 'Needs acknowledgement'}
                  detail="still open" />
              </View>
              <T variant="caption" muted>For: {i.audiences.join(', ').replace('next_operator', 'next operator')}</T>
            </Row>
          ))}
        </View>
      </Section>
      <Section title="Today">
        <T>{snap.briefing.task_count} tasks. Next: {next ? `${next.task.task_type.replace('_', ' ')} at ${next.zone_name ?? next.task.location_text}` : 'none'}.
          {snap.day_finish ? ` Expected day finish ${clock(snap.day_finish.p50_at, offset)}; late case ${clock(snap.day_finish.p90_at, offset)}.` : ''}</T>
      </Section>
      <Section title="Conditions">
        <View style={{ flexDirection: 'row', gap: space.md, alignItems: 'center' }}>
          <T>{snap.briefing.conditions_text}</T>
          {snap.briefing.conditions_old ? <StateFlag tone="caution" word="Old report" /> : null}
        </View>
      </Section>
      {snap.briefing.risk_notes.length ? (
        <Section title="Today's risk notes">
          {snap.briefing.risk_notes.map((n) => <T key={n}>• {n}</T>)}
        </Section>
      ) : null}
      <Row focused={focus === items.length} disabled={!allAck} onPress={() => allAck && router.replace('/tasks')}>
        <T variant="heading">Continue to tasks</T>
        {!allAck ? <T variant="caption" muted>Acknowledge every item first (acknowledging does not resolve it)</T> : null}
      </Row>
      </View>
      </WorkSurface>
    </Screen>
  );
}
