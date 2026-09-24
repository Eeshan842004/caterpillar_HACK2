import { View } from 'react-native';
import { useHost } from '../src/engine/host';
import { useKeys } from '../src/input/keys';
import { ActionBar, InstrumentValue, StateFlag, T, WorkSurface, usePalette } from '../src/ui/components';
import { SafetyGroup } from '../src/ui/safety';
import { clock, taskLabel } from '../src/ui/format';
import { space, type } from '../src/ui/tokens';

export default function Focus() {
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
  const v = snap.tasks.find((t) => t.task.task_id === snap.active_task_id);
  const offset = snap.site.utc_offset_minutes;
  return <View style={{ flex: 1, backgroundColor: p.bg }}>
    {snap.machine.state === 'UNKNOWN' ? <View style={{ padding: space.md }}><StateFlag tone="unavailable" word="Machine state unknown" detail="Some signals are missing" /></View> : null}
    <View style={{ flex: 1, margin: space.lg, borderWidth: 1, borderColor: p.border }}>
      <WorkSurface>
        <View style={{ padding: space.xl, borderBottomWidth: 1, borderColor: p.border }}>
          <T variant="heading" muted>Current task</T>
          {v ? <>
            <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: space.lg, flexWrap: 'wrap' }}>
              <T variant="title" style={{ flex: 1 }}>{taskLabel(v.task.task_type)} at {v.zone_name ?? v.task.location_text}</T>
              <T style={type.valueL}>{v.progress} / {v.task.quantity} {v.task.unit}</T>
            </View>
            <View style={{ height: 14, backgroundColor: p.surfaceAlt, marginTop: space.md }}>
              <View style={{ height: 14, width: `${v.live?.progressPct ?? 0}%`, backgroundColor: p.focus }} />
            </View>
          </> : <T variant="title">No active task. Stop to choose one.</T>}
        </View>
        <View style={{ flex: 1, flexDirection: 'row', flexWrap: 'wrap' }}>
          <View style={{ flex: 3, minWidth: 320, borderRightWidth: 1, borderColor: p.border }}>
            {v?.live ? v.live.mode === 'conditional'
              ? <InstrumentValue label="Expected finish" value={`~${Math.round(v.live.rem50)}`} unit="min after resume" />
              : <InstrumentValue label="Expected finish" value={clock(v.live.finish50, offset)} range={`${clock(v.live.finish10, offset)}–${clock(v.live.finish90, offset)}`} />
              : <InstrumentValue label="Expected finish" value="—" />}
          </View>
          <View style={{ flex: 2, minWidth: 300, padding: space.xl }}><T variant="heading" muted style={{ marginBottom: space.md }}>Safety</T><SafetyGroup /></View>
        </View>
      </WorkSurface>
    </View>
    <ActionBar hints="Menus locked while operating · Space ACK alert · F2 presenter" />
  </View>;
}
