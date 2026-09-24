// A5 Focus Mode (F5-R1, R3): one tile, three groups — task + progress, finish time, safety (belt, proximity, idle).
// Menus are locked; only ACK, PTT and SOS work (handled globally).
import { View } from 'react-native';
import { useHost } from '../src/engine/host';
import { useKeys } from '../src/input/keys';
import { ActionBar, StatusPill, T, usePalette } from '../src/ui/components';
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
  return (
    <View style={{ flex: 1, backgroundColor: p.bg }}>
      {snap.machine.state === 'UNKNOWN' ? (
        <View style={{ padding: space.md }}><StatusPill tone="unavailable" word="Machine state unknown" detail="some signals missing" /></View>
      ) : null}
      <View style={{ flex: 1, margin: space.lg, padding: space.xl, borderRadius: 16, backgroundColor: p.surface, gap: space.xl }}>
        <View>
          <T variant="heading" muted>TASK</T>
          {v ? (
            <>
              <T variant="title">{taskLabel(v.task.task_type)} · {v.zone_name ?? v.task.location_text}</T>
              <T style={type.valueL}>{v.progress} / {v.task.quantity} {v.task.unit}</T>
              <View style={{ height: 16, backgroundColor: p.surfaceAlt, borderRadius: 8 }}>
                <View style={{ height: 16, width: `${v.live?.progressPct ?? 0}%`, backgroundColor: p.focus, borderRadius: 8 }} />
              </View>
            </>
          ) : <T variant="title">No active task. Stop to choose one.</T>}
        </View>
        <View>
          <T variant="heading" muted>FINISH</T>
          {v?.live ? (
            v.live.mode === 'conditional'
              ? <T style={type.valueL}>~{Math.round(v.live.rem50)} min after resume</T>
              : <>
                  <T style={type.display}>{clock(v.live.finish50, offset)}</T>
                  <T variant="heading">{clock(v.live.finish10, offset)}–{clock(v.live.finish90, offset)}</T>
                </>
          ) : <T variant="title">—</T>}
        </View>
        <View>
          <T variant="heading" muted>SAFETY</T>
          <SafetyGroup />
        </View>
      </View>
      <ActionBar hints="Menus locked while operating · Space ACK alert · F2 presenter" />
    </View>
  );
}
