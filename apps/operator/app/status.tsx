// A14 Status (subset): connectivity, records waiting, signal health, alert history, alert budget (NFR-17), versions.
import { useRouter } from 'expo-router';
import { View } from 'react-native';
import { useHost } from '../src/engine/host';
import { Row, Screen, Section, StatusPill, T } from '../src/ui/components';
import { useFocusList } from '../src/ui/useFocusList';
import { space } from '../src/ui/tokens';

export default function Status() {
  const router = useRouter();
  const snap = useHost((s) => s.snapshot);
  useFocusList(1, () => router.replace('/tasks'), (k) => {
    if (k.action === 'BACK') router.replace('/tasks');
    else return false;
    return true;
  });
  if (!snap) return null;
  const hour = snap.alerts.budget.at(-1);
  return (
    <Screen title="Status & sync" hints="Back or OK returns to tasks">
      <Section title="Connectivity">
        <View style={{ gap: space.sm }}><T>Connection: Local only</T><T>{snap.pending_sync} records waiting</T><T>{snap.ledger_count} ledger entries on this device</T></View>
        <T muted>This build has no site-server connection. Keep the app open to retain this session.</T>
      </Section>
      <Section title="Signal health">
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space.sm }}>
          {snap.signal_health.map((h) => (
            <StatusPill key={h.name} tone={h.fresh ? 'ok' : 'unavailable'} word={h.name}
              detail={h.fresh ? `${Math.round((h.age_ms ?? 0) / 100) / 10} s` : 'Unavailable'} />
          ))}
        </View>
      </Section>
      <Section title="Alert budget (this hour)">
        {hour ? <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space.xl }}><T>{hour.alerts_raised} raised</T><T>{hour.repeats_spoken} repeats</T><T>{hour.repeats_suppressed_after_ack} suppressed after acknowledgement</T><T>{hour.duplicate_raises_prevented} duplicates prevented</T><T>{hour.noncritical_prompts_deferred} prompts deferred</T><T>{hour.acknowledged} acknowledged</T><T>{hour.resolved} cleared</T><T>{Math.round(hour.operating_s / 60)} operating min</T></View>
          : <T muted>No operating time yet.</T>}
      </Section>
      <Section title="Active alerts">
        {snap.alerts.active.length ? snap.alerts.active.map((a) => <View key={a.alert_id} style={{ flexDirection: 'row', gap: space.xl, flexWrap: 'wrap' }}><T>{a.level}</T><T>{a.alert_type}</T><T>{a.status}</T><T>{a.occurrences} occurrences</T></View>)
          : <T muted>None</T>}
      </Section>
      <Section title="Versions">
        <View style={{ gap: space.sm }}><T muted>Profile {snap.machine.profile_id}@{snap.machine.profile_version}</T><T muted>Estimator: baseline fallback</T><T muted>Voice: unavailable in this build</T><T muted>Alert audio: device text-to-speech</T></View>
      </Section>
      <Row focused onPress={() => router.replace('/tasks')}><T variant="heading">Back to tasks</T></Row>
    </Screen>
  );
}
