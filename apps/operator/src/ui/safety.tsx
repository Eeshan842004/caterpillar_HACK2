// Safety group shared by Focus Mode (A5) and Drive Mode (A6): belt, proximity, idle — colour + icon + word.
import { View } from 'react-native';
import { useHost } from '../engine/host';
import { StatusPill } from './components';
import { space } from './tokens';

export function SafetyGroup() {
  const snap = useHost((s) => s.snapshot);
  if (!snap) return null;
  const prox = snap.proximity;
  const belt = snap.belt;
  return (
    <View style={{ flexDirection: 'row', gap: space.md, flexWrap: 'wrap' }}>
      <StatusPill tone={belt === 'fastened' ? 'ok' : belt === 'unfastened' ? 'warning' : 'unavailable'}
        word={belt === 'fastened' ? 'Belt fastened' : belt === 'unfastened' ? 'Belt UNFASTENED' : 'Belt unavailable'} />
      {prox.status === 'alert'
        ? <StatusPill tone={prox.level === 'CAUTION' ? 'caution' : prox.level === 'CRITICAL' ? 'critical' : 'warning'}
          word={`${prox.object_type.replace('_', ' ')} · ${prox.place.replace('_', ' ')}`} detail={`${prox.distance_m} m`} />
        : <StatusPill tone={prox.status === 'clear' ? 'ok' : 'unavailable'} word={prox.status === 'clear' ? 'Proximity clear' : 'Proximity unavailable'} />}
      {snap.idle ? <StatusPill tone="info" word="Idle" detail={`${Math.floor(snap.idle.elapsed_s / 60)}:${String(snap.idle.elapsed_s % 60).padStart(2, '0')}`} /> : null}
    </View>
  );
}

