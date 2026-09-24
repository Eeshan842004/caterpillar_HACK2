// A1 Sign-in (F1-R1): pick the operator with Up/Down, type a 4–6 digit PIN with digit keys, OK submits.
// Key 3 = "Key fob (simulated)": signs in the highlighted operator without a PIN.
import { useMemo, useState } from 'react';
import { Pressable, View } from 'react-native';
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
  const addDigit = (digit: number) => {
    setPinMode(true);
    setPin((value) => value.length < 6 ? value + String(digit) : value);
    setError(null);
  };
  const submitPin = () => {
    if (!op) return;
    const result = host.dispatch({ type: 'SIGN_IN', operator_id: op.operator_id, pin });
    if (!result.ok) setError(result.message ?? 'PIN not recognised');
    setPin('');
  };

  useKeys((k) => {
    if (pinMode) {
      if (k.digit !== null && pin.length < 6) {
        setPin((x) => x + String(k.digit));
        setError(null);
      } else if (k.action === 'BACK') {
        if (pin.length) setPin((x) => x.slice(0, -1));
        else setPinMode(false);
      } else if (k.action === 'OK' && op) {
        submitPin();
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
    <Screen title="Operator sign in"
      hints={pinMode ? 'Digits type PIN · OK sign in · Back delete' : 'Up/Down choose · OK enter PIN · 3 key fob (simulated)'}>
      <View style={{ borderLeftWidth: 8, borderColor: p.attention, paddingLeft: space.lg }}>
        <T variant="title">{snap.machine.machine_id}</T>
        <T>{snap.machine.display_name}</T>
        <T muted>{snap.site.name}</T>
      </View>
      <View style={{ flexDirection: 'row', gap: space.xl, flexWrap: 'wrap' }}>
        <View style={{ flex: 3, gap: space.sm }}>
          {operators.map((o, i) => (
            <Row key={o.operator_id} focused={!pinMode && i === focus} onPress={() => { setFocus(i); setPinMode(true); }}>
              <T variant="heading">{o.display_name}</T>
              <View style={{ flexDirection: 'row', gap: space.xl, flexWrap: 'wrap' }}><T muted>{o.operator_id}</T><T muted>{o.skill_level}</T><T muted>{o.language}</T></View>
            </Row>
          ))}
        </View>
        <View style={{ flex: 2, minWidth: 300, backgroundColor: p.surface, borderTopWidth: 4, borderColor: p.focus, padding: space.xl, gap: space.md, alignSelf: 'flex-start' }}>
          <T variant="heading">{op ? `PIN for ${op.display_name}` : 'PIN'}</T>
          <T style={[type.display, { letterSpacing: 12 }]}>{pinMode ? '●'.repeat(pin.length).padEnd(4, '○') : '○○○○'}</T>
          {lockedUntil ? <StatusPill tone="critical" word="Locked" detail={`${Math.ceil((lockedUntil - snap.now) / 1000)} s`} />
            : error ? <StatusPill tone="critical" word={error} /> : null}
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: space.sm }}>
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 0].map((digit) => (
              <Pressable key={digit} onPress={() => addDigit(digit)} style={{ width: 64, height: 56, alignItems: 'center', justifyContent: 'center', backgroundColor: p.surfaceAlt, borderWidth: 1, borderColor: p.border, borderRadius: 4 }}>
                <T variant="heading">{digit}</T>
              </Pressable>
            ))}
          </View>
          <View style={{ flexDirection: 'row', gap: space.sm }}>
            <Pressable onPress={() => setPin((value) => value.slice(0, -1))} style={{ minHeight: 56, flex: 1, alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: p.border, borderRadius: 4 }}><T variant="label">Delete</T></Pressable>
            <Pressable disabled={pin.length < 4 || !!lockedUntil} onPress={submitPin} style={{ minHeight: 56, flex: 2, alignItems: 'center', justifyContent: 'center', backgroundColor: p.primaryBg, borderRadius: 4, opacity: pin.length < 4 || lockedUntil ? 0.45 : 1 }}><T variant="label" style={{ color: p.onPrimary }}>Sign in</T></Pressable>
          </View>
          <T muted>Enter 4–6 digits. Demo PIN: 1234.</T>
        </View>
      </View>
    </Screen>
  );
}
