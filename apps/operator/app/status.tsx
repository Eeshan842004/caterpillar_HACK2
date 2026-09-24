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
        <T>Local only (not paired with a server) · {snap.pending_sync} records waiting · {snap.ledger_count} ledger entries on this device</T>
        <T muted>Server sync (T22) and on-device SQLite storage (T16) arrive in the next slice; records are kept in memory for this build.</T>
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
        {hour ? <T>{hour.alerts_raised} raised · {hour.repeats_spoken} repeats · {hour.repeats_suppressed_after_ack} repeats suppressed after ACK · {hour.duplicate_raises_prevented} duplicates prevented · {hour.noncritical_prompts_deferred} prompts deferred · {hour.acknowledged} acknowledged · {hour.resolved} cleared · {Math.round(hour.operating_s / 60)} operating min</T>
          : <T muted>No operating time yet.</T>}
      </Section>
      <Section title="Active alerts">
        {snap.alerts.active.length ? snap.alerts.active.map((a) => <T key={a.alert_id}>{a.level} · {a.alert_type} · {a.status} · ×{a.occurrences}</T>)
          : <T muted>None</T>}
      </Section>
      <Section title="Versions">
        <T muted>Profile {snap.machine.profile_id}@{snap.machine.profile_version} · estimator: baseline fallback (trained artifact not installed) · voice: not in this build · alert audio: device text-to-speech (recorded clips E-05 not installed)</T>
      </Section>
      <Row focused onPress={() => router.replace('/tasks')}><T variant="heading">Back to tasks</T></Row>
    </Screen>
  );
}
