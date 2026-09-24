// Safety group shared by Focus Mode (A5) and Drive Mode (A6): belt, proximity, idle — colour + icon + word.
import { View } from 'react-native';
import { useHost } from '../engine/host';
import { StateFlag } from './components';
import { space } from './tokens';

export function SafetyGroup() {
  const snap = useHost((s) => s.snapshot);
  if (!snap) return null;
  const prox = snap.proximity;
  const belt = snap.belt;
  return (
    <View style={{ gap: space.sm }}>
      <StateFlag icon="belt" tone={belt === 'fastened' ? 'ok' : belt === 'unfastened' ? 'warning' : 'unavailable'}
        word={belt === 'fastened' ? 'Belt fastened' : belt === 'unfastened' ? 'Belt unfastened' : 'Belt unavailable'} />
      {prox.status === 'alert'
        ? <StateFlag icon="proximity" tone={prox.level === 'CAUTION' ? 'caution' : prox.level === 'CRITICAL' ? 'critical' : 'warning'}
          word={`${prox.object_type.replace('_', ' ')} at ${prox.place.replace('_', ' ')}`} detail={`${prox.distance_m} m`} />
        : <StateFlag icon="proximity" tone={prox.status === 'clear' ? 'ok' : 'unavailable'} word={prox.status === 'clear' ? 'Proximity clear' : 'Proximity unavailable'} />}
      {snap.idle ? <StateFlag icon="idle" tone="info" word="Idle" detail={`${Math.floor(snap.idle.elapsed_s / 60)}:${String(snap.idle.elapsed_s % 60).padStart(2, '0')}`} /> : null}
    </View>
  );
}
