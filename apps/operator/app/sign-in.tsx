// A1 Sign-in (F1-R1): pick the operator with Up/Down, type a 4–6 digit PIN with digit keys, OK submits.
// Key 3 = "Key fob (simulated)": signs in the highlighted operator without a PIN.
import { useMemo, useState } from 'react';
import { View } from 'react-native';
import { host, useHost } from '../src/engine/host';
import { useKeys } from '../src/input/keys';
import { Row, Screen, StatusPill, T, usePalette } from '../src/ui/components';
import { space, type } from '../src/ui/tokens';

export default function SignIn() {
  const p = usePalette();
  const snap = useHost((s) => s.snapshot);
  const machineId = snap?.machine.machine_id;
  const operators = useMemo(() => host.engine?.roster() ?? [], [machineId]);
  const [focus, setFocus] = useState(0);
  const [pinMode, setPinMode] = useState(false);
  const [pin, setPin] = useState('');
  const [error, setError] = useState<string | null>(null);
  const op = operators[focus];
  const lockedUntil = op ? snap?.pin_lockout_until[op.operator_id] : undefined;

  useKeys((k) => {
    if (pinMode) {
      if (k.digit !== null && pin.length < 6) {
        setPin((x) => x + String(k.digit));
        setError(null);
      } else if (k.action === 'BACK') {
        if (pin.length) setPin((x) => x.slice(0, -1));
        else setPinMode(false);
      } else if (k.action === 'OK' && op) {
        const r = host.dispatch({ type: 'SIGN_IN', operator_id: op.operator_id, pin });
        if (!r.ok) setError(r.message ?? 'PIN not recognised');
        setPin('');
      } else return false;
      return true;
    }
    if (k.action === 'UP') setFocus((f) => Math.max(0, f - 1));
    else if (k.action === 'DOWN') setFocus((f) => Math.min(operators.length - 1, f + 1));
    else if (k.action === 'OK' || k.action === 'RIGHT') setPinMode(true);
    else if (k.action === 'QUICK_3' && op) host.dispatch({ type: 'SIGN_IN_FOB', operator_id: op.operator_id });
    else return false;
    return true;
  });

  if (!snap) return null;
  if (operators.length === 0) {
    return (
      <Screen title="Sign in" hints="Presenter (F2): Switch machine to re-pair">
        <StatusPill tone="critical" word="No operators on this device" detail="Open device setup" />
      </Screen>
    );
  }
  return (
    <Screen title={`${snap.machine.machine_id} · ${snap.machine.display_name} · ${snap.site.name}`}
      hints={pinMode ? 'Digits type PIN · OK sign in · Back delete' : 'Up/Down choose · OK enter PIN · 3 key fob (simulated)'}>
      <View style={{ flexDirection: 'row', gap: space.xl }}>
        <View style={{ flex: 3, gap: space.sm }}>
          {operators.map((o, i) => (
            <Row key={o.operator_id} focused={!pinMode && i === focus} onPress={() => { setFocus(i); setPinMode(true); }}>
              <T variant="heading">{o.display_name}</T>
              <T muted>{o.operator_id} · {o.skill_level} · {o.language}</T>
            </Row>
          ))}
        </View>
        <View style={{ flex: 2, backgroundColor: p.surface, borderRadius: 12, padding: space.xl, gap: space.md, alignSelf: 'flex-start' }}>
          <T variant="heading">{op ? `PIN for ${op.display_name}` : 'PIN'}</T>
          <T style={[type.display, { letterSpacing: 12 }]}>{pinMode ? '●'.repeat(pin.length).padEnd(4, '○') : '○○○○'}</T>
          {lockedUntil ? <StatusPill tone="critical" word="Locked" detail={`${Math.ceil((lockedUntil - snap.now) / 1000)} s`} />
            : error ? <StatusPill tone="critical" word={error} /> : null}
          <T muted>4–6 digits · keyboard digits or controller number pad</T>
        </View>
      </View>
    </Screen>
  );
}
