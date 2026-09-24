import { View } from 'react-native';
import { useHost } from '../src/engine/host';
import { useKeys } from '../src/input/keys';
import { ActionBar, StateFlag, T, WorkSurface, usePalette } from '../src/ui/components';
import { SafetyGroup } from '../src/ui/safety';
import { space, type } from '../src/ui/tokens';

export default function Drive() {
  const p = usePalette();
  const snap = useHost((s) => s.snapshot);
  useKeys((k) => {
    if (k.action === 'OK' || k.action === 'BACK' || k.action === 'MENU' || k.action?.startsWith('QUICK_')) {
      useHost.setState({ lastMessage: 'Menus locked while operating' });
      return true;
    }
    return false;
  });
  if (!snap) return null;
  const { speed_kmh, limit_kmh, over } = snap.speed;
  const next = snap.tasks.find((t) => t.task.task_id === snap.active_task_id) ?? snap.tasks.find((t) => t.is_next);
  return <View style={{ flex: 1, backgroundColor: p.bg }}>
    <View style={{ flex: 1, margin: space.lg, borderWidth: 1, borderColor: p.border }}><WorkSurface>
      <View style={{ flex: 3, padding: space.xl, flexDirection: 'row', alignItems: 'center', gap: space.xl, borderBottomWidth: 1, borderColor: p.border }}>
        <T style={[type.instrumentXL, { fontSize: 132, lineHeight: 132, color: over ? p.status.critical.bg : p.text }]}>{speed_kmh === null ? '—' : Math.round(speed_kmh)}</T>
        <View><T variant="heading">km/h</T><T variant="title">Limit {limit_kmh === null ? '—' : Math.round(limit_kmh)}</T>{over ? <StateFlag tone="critical" word="Over limit" /> : null}</View>
      </View>
      <View style={{ flex: 2, flexDirection: 'row', flexWrap: 'wrap' }}>
        <View style={{ flex: 1, minWidth: 300, padding: space.xl, borderRightWidth: 1, borderColor: p.border }}><T variant="heading" muted>Next stop</T><T variant="title">{next ? next.zone_name ?? next.task.location_text : '—'}</T></View>
        <View style={{ flex: 1, minWidth: 300, padding: space.xl }}><T variant="heading" muted style={{ marginBottom: space.md }}>Proximity</T><SafetyGroup /></View>
      </View>
    </WorkSurface></View>
    <ActionBar hints="Menus locked while driving · Space ACK alert" />
  </View>;
}
