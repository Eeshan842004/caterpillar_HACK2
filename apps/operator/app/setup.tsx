// A0 Device setup (SD-07): installer pairs the tablet to one machine. Slice 1 supports "Local only" pairing.
import { host, PAIRABLE_MACHINES } from '../src/engine/host';
import { Row, Screen, T } from '../src/ui/components';
import { useFocusList } from '../src/ui/useFocusList';

export default function Setup() {
  const [focus] = useFocusList(PAIRABLE_MACHINES.length, (i) => {
    const m = PAIRABLE_MACHINES[i];
    if (m) host.pair(m.machine_id);
  });
  return (
    <Screen title="Device setup — pair this tablet" hints="Up/Down choose machine · OK pair (Local only)">
      <T muted>Local only: the seeded roster, tasks and content are used with no server. Server pairing arrives with sync (T22).</T>
      {PAIRABLE_MACHINES.map((m, i) => (
        <Row key={m.machine_id} focused={i === focus} onPress={() => host.pair(m.machine_id)}>
          <T variant="heading">{m.machine_id} · {m.profile_name}</T>
          <T muted>{m.model_name} · {m.site_name}</T>
        </Row>
      ))}
    </Screen>
  );
}
