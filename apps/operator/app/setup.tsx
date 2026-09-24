// A0 Device setup (SD-07): the installer pairs the tablet to one machine — with the site server (server address +
// pairing code; tasks, roster, forecast and the trained estimator come from the server and records sync back), or in
// "Local only" mode from the data stored on the tablet.
import { useEffect, useState } from 'react';
import { TextInput, View } from 'react-native';
import { host, PAIRABLE_MACHINES, useHost } from '../src/engine/host';
import { lastServerUrl } from '../src/sync/client';
import { Row, Screen, Section, StatusPill, T, usePalette } from '../src/ui/components';
import { radius, space, type } from '../src/ui/tokens';
import { useFocusList } from '../src/ui/useFocusList';

export default function Setup() {
  const p = usePalette();
  const connecting = useHost((s) => s.connecting);
  const error = useHost((s) => s.connectError);
  const [mode, setMode] = useState<'server' | 'local'>('server');
  const [url, setUrl] = useState(lastServerUrl);
  const [code, setCode] = useState('');

  useEffect(() => {
    void host.resume(); // reconnect a saved pairing after a reload
  }, []);

  const choose = (i: number) => {
    if (i === 0) {
      setMode((m) => (m === 'server' ? 'local' : 'server'));
      return;
    }
    const m = PAIRABLE_MACHINES[i - 1];
    if (!m || connecting) return;
    if (mode === 'local') host.pair(m.machine_id);
    else void host.connectServer(url, code || m.demo_code, m.machine_id);
  };
  const [focus] = useFocusList(PAIRABLE_MACHINES.length + 1, choose);
  const input = [type.body, { color: p.text, backgroundColor: p.surface, borderColor: p.border, borderWidth: 1,
    borderRadius: radius.control, paddingHorizontal: space.md, paddingVertical: space.sm, minHeight: 48 }];

  return (
    <Screen title="Device setup — pair this tablet" hints="Up/Down choose · OK pair or switch mode">
      <Section title="Connection">
        <Row focused={focus === 0} onPress={() => choose(0)}>
          <T variant="heading">{mode === 'server' ? 'Site server' : 'Local only (no server)'}</T>
          <T muted>{mode === 'server'
            ? 'Tasks, roster and estimates come from the server; records sync back. OK switches to local only.'
            : 'Uses the data stored on this tablet; nothing is sent. OK switches to site server.'}</T>
        </Row>
        {mode === 'server' ? (
          <View style={{ gap: space.sm }}>
            <T muted>Server address (shown by the laptop's demo command)</T>
            <TextInput value={url} onChangeText={setUrl} placeholder="http://192.168.1.10:8000" autoCapitalize="none"
              autoCorrect={false} keyboardType="url" placeholderTextColor={p.textMuted} style={input} />
            <T muted>Pairing code (leave empty to use the demo code shown for each machine)</T>
            <TextInput value={code} onChangeText={setCode} placeholder="e.g. 100007" keyboardType="number-pad"
              placeholderTextColor={p.textMuted} style={input} />
          </View>
        ) : null}
      </Section>
      {connecting ? <StatusPill tone="info" word="Connecting" detail={connecting} /> : null}
      {error ? <StatusPill tone="warning" word="Could not connect" detail={error} /> : null}
      <Section title="Machine">
        {PAIRABLE_MACHINES.map((m, i) => (
          <Row key={m.machine_id} focused={focus === i + 1} disabled={!!connecting} onPress={() => choose(i + 1)}>
            <T variant="heading">{m.machine_id}</T>
            <T>{m.profile_name}</T>
            <T muted>{m.model_name} · {m.site_name}</T>
            {mode === 'server' && m.demo_code ? <T muted>Demo pairing code {m.demo_code}</T> : null}
          </Row>
        ))}
      </Section>
    </Screen>
  );
}
