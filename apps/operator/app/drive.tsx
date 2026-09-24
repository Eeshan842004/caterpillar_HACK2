// A6 Drive Mode (F5-R2): speed vs limit, next stop, proximity only.
import { View } from 'react-native';
import { useHost } from '../src/engine/host';
import { useKeys } from '../src/input/keys';
import { ActionBar, StatusPill, T, usePalette } from '../src/ui/components';
import { space, type } from '../src/ui/tokens';
import { SafetyGroup } from '../src/ui/safety';

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
  return (
    <View style={{ flex: 1, backgroundColor: p.bg }}>
      <View style={{ flex: 1, margin: space.lg, padding: space.xl, borderRadius: 16, backgroundColor: p.surface, gap: space.xl }}>
        <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: space.xl }}>
          <T style={[type.display, { fontSize: 120, lineHeight: 128, color: over ? p.status.critical.bg : p.text }]}>
            {speed_kmh === null ? '—' : Math.round(speed_kmh)}
          </T>
          <View>
            <T variant="heading">km/h</T>
            <T variant="title">Limit {limit_kmh === null ? '—' : Math.round(limit_kmh)}</T>
            {over ? <StatusPill tone="critical" word="OVER" /> : null}
          </View>
        </View>
        <View>
          <T variant="heading" muted>NEXT STOP</T>
          <T variant="title">{next ? next.zone_name ?? next.task.location_text : '—'}</T>
        </View>
        <View>
          <T variant="heading" muted>PROXIMITY</T>
          <SafetyGroup />
        </View>
      </View>
      <ActionBar hints="Menus locked while driving · Space ACK alert" />
    </View>
  );
}
