import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useHost } from '../engine/host';
import { useSync } from '../sync/client';
import { Icon, TONE_ICON, type IconName } from './icons';
import { day, night, radius, type Palette, space, type StatusTone, type } from './tokens';

export function usePalette(): Palette {
  const local = useHost((s) => s.snapshot?.local_time);
  const hour = local ? Number(local.slice(0, 2)) : 12;
  return hour >= 19 || hour < 6 ? night : day;
}

export function StateFlag({ tone, word, detail, icon }: { tone: StatusTone; word: string; detail?: string; icon?: IconName }) {
  const p = usePalette();
  const c = p.status[tone];
  return <View style={[styles.flag, { backgroundColor: c.bg }]} accessibilityLabel={`${word}${detail ? `, ${detail}` : ''}`}>
    <Icon name={icon ?? TONE_ICON[tone]} color={c.fg} size={22} />
    <Text style={[type.label, { color: c.fg }]}>{word}</Text>
    {detail ? <Text style={[type.caption, styles.flagDetail, { color: c.fg }]}>{detail}</Text> : null}
  </View>;
}

/** Backwards-compatible name while screens migrate to the semantic primitive. */
export const StatusPill = StateFlag;

export function SourceMark({ source }: { source: 'observed' | 'reported' | 'inferred' | 'reviewed' }) {
  const p = usePalette();
  const word = { observed: 'Observed', reported: 'Reported', inferred: 'Inferred', reviewed: 'Reviewed' }[source];
  return <View style={[styles.source, { borderColor: p.provenance[source] }]}><Text style={[type.caption, { color: p.text }]}>{word}</Text></View>;
}
export const ProvenanceTag = SourceMark;

export function Row({ focused, disabled, onPress, attention, children }: { focused: boolean; disabled?: boolean; onPress?: () => void; attention?: boolean; children: ReactNode }) {
  const p = usePalette();
  return <Pressable onPress={disabled ? undefined : onPress} style={({ pressed }) => [
    styles.row, { backgroundColor: pressed ? p.surfaceAlt : p.surface, borderColor: focused ? p.focus : p.border, opacity: disabled ? 0.5 : 1 },
    focused && styles.rowFocused,
  ]} accessibilityState={{ selected: focused, disabled }}>
    <View style={[styles.rowMarker, { backgroundColor: attention ? p.attention : focused ? p.focus : 'transparent' }]} />
    <View style={{ flex: 1 }}>{children}</View>
  </Pressable>;
}
export const FocusRow = Row;

export function T({ children, style, muted, variant = 'body', numberOfLines }: { children: ReactNode; style?: object | object[]; muted?: boolean; variant?: keyof typeof type; numberOfLines?: number }) {
  const p = usePalette();
  return <Text numberOfLines={numberOfLines} style={[type[variant], { color: muted ? p.textMuted : p.text }, style]}>{children}</Text>;
}

export function RuledGroup({ title, children }: { title?: string; children: ReactNode }) {
  const p = usePalette();
  return <View style={[styles.group, { borderColor: p.border }]}>
    {title ? <T variant="heading" style={styles.groupTitle}>{title}</T> : null}
    {children}
  </View>;
}
export const Section = RuledGroup;

export function WorkSurface({ children, split = false }: { children: ReactNode; split?: boolean }) {
  const p = usePalette();
  const { width } = useWindowDimensions();
  return <View style={[styles.workSurface, { backgroundColor: p.surface, flexDirection: split && width >= 760 ? 'row' : 'column' }]}>{children}</View>;
}

export function InstrumentValue({ label, value, unit, range }: { label: string; value: string | number; unit?: string; range?: string }) {
  return <View style={styles.instrument}>
    <T variant="heading" muted>{label}</T>
    <View style={styles.valueLine}><T variant="display">{value}</T>{unit ? <T variant="heading" style={{ marginBottom: 7 }}>{unit}</T> : null}</View>
    {range ? <T variant="heading">{range}</T> : null}
  </View>;
}

export function ContinuityRail({ stops, active = 0 }: { stops: { label: string; detail?: string }[]; active?: number }) {
  const p = usePalette();
  return <View style={styles.continuity} accessibilityRole="list">
    {stops.map((stop, index) => <View key={`${stop.label}-${index}`} style={styles.stop}>
      <View style={[styles.stopLine, { backgroundColor: index <= active ? p.attention : p.border }]} />
      <View style={[styles.stopNode, { borderColor: index === active ? p.attention : p.border, backgroundColor: index === active ? p.attention : p.surface }]} />
      <View style={{ flex: 1, paddingBottom: space.lg }}><T variant="label">{stop.label}</T>{stop.detail ? <T variant="caption" muted>{stop.detail}</T> : null}</View>
    </View>)}
  </View>;
}

export function Screen({ title, hints, children, scroll = true }: { title: string; hints: string; children: ReactNode; scroll?: boolean }) {
  const p = usePalette();
  const { width } = useWindowDimensions();
  const body = <View style={[styles.screenBody, { maxWidth: 1280, paddingHorizontal: width < 600 ? space.md : space.xl }]}>{children}</View>;
  return <View style={{ flex: 1, backgroundColor: p.bg }}>
    <View style={[styles.screenTitle, { borderColor: p.border }]}><T variant="title">{title}</T></View>
    {scroll ? <ScrollView style={{ flex: 1 }} contentContainerStyle={{ alignItems: 'center' }}>{body}</ScrollView> : <View style={{ flex: 1, alignItems: 'center' }}>{body}</View>}
    <ActionBar hints={hints} />
  </View>;
}

function hintParts(hints: string): { key: string; action: string }[] {
  return hints.split(/\s*[·•]\s*/).filter(Boolean).map((part) => {
    const match = /^(Up\/Down|Back|OK|ACK|Space|Digits|[1-4](?:–[1-4])?|M|F2|last row:?)\s*(.*)$/i.exec(part.trim());
    return match ? { key: match[1] ?? '', action: match[2] || '' } : { key: '', action: part.trim() };
  });
}

export function ActionBar({ hints }: { hints: string }) {
  const p = usePalette();
  const msg = useHost((s) => s.lastMessage);
  return <View style={[styles.actionBar, { backgroundColor: p.rail }]}>
    <View style={styles.actions}>{hintParts(hints).map((part, i) => <View key={`${part.key}-${i}`} style={styles.actionPair}>
      {part.key ? <Text style={[type.label, styles.key, { color: p.rail }]}>{part.key}</Text> : null}
      <Text style={[type.label, { color: p.onPrimary }]}>{part.action}</Text>
    </View>)}</View>
    {msg ? <View style={styles.feedback}><Icon name="warning" color={p.onPrimary} size={20} /><Text style={[type.label, { color: p.onPrimary }]} numberOfLines={2}>{msg}</Text></View> : null}
  </View>;
}

export function AppStatusBar() {
  const p = usePalette();
  const snap = useHost((s) => s.snapshot);
  const sync = useSync();
  const openPresenter = () => useHost.setState((s) => ({ presenterOpen: !s.presenterOpen }));
  const toggleVoice = () => useHost.setState((s) => ({ voiceOpen: !s.voiceOpen, menuOpen: false }));
  const toggleMenu = () => useHost.setState((s) => ({ menuOpen: !s.menuOpen, voiceOpen: false }));
  const openSos = () => useHost.setState({ sosOpen: true, menuOpen: false, voiceOpen: false });
  const link = sync.mode === 'local' ? { icon: 'offline' as const, text: 'Local only' }
    : sync.online ? { icon: 'check' as const, text: 'Online' } : { icon: 'offline' as const, text: 'Offline' };
  if (!snap) return null;
  const unavailable = snap.signal_health.filter((h) => !h.fresh).length;
  const stateTone: StatusTone = snap.machine.state === 'UNKNOWN' ? 'unavailable' : snap.machine.state === 'WORKING' || snap.machine.state === 'TRAVELLING' ? 'info' : 'ok';
  return <View style={[styles.machineRail, { backgroundColor: p.rail }]}>
    <View style={styles.machineSlot}><Icon name={link.icon} color={p.onPrimary} size={20} /><Text style={[type.label, { color: p.onPrimary }]}>{link.text}</Text></View>
    <Text style={[type.caption, { color: p.onPrimary }]}>{snap.pending_sync} waiting</Text>
    <View style={styles.machineSlot}><Icon name={unavailable ? 'unavailable' : 'sensor'} color={p.onPrimary} size={20} /><Text style={[type.caption, { color: p.onPrimary }]}>{unavailable ? `${unavailable} unavailable` : 'Sensors clear'}</Text></View>
    <View style={[styles.machineState, { backgroundColor: p.status[stateTone].bg }]}><Icon name={TONE_ICON[stateTone]} color={p.status[stateTone].fg} size={18} /><Text style={[type.caption, { color: p.status[stateTone].fg }]}>{snap.machine.state.toLowerCase()}</Text></View>
    <View style={{ flex: 1 }} />
    <Text style={[type.label, { color: p.onPrimary }]}>{snap.machine.machine_id}</Text>
    {snap.shift ? <Pressable accessibilityRole="button" onPress={toggleVoice} style={styles.railButton}><Icon name="info" color={p.rail} size={18} /><Text style={[type.label, { color: p.rail }]}>Voice</Text></Pressable> : null}
    {snap.shift ? <Pressable accessibilityRole="button" onPress={toggleMenu} style={styles.railButton}><Text style={[type.label, { color: p.rail }]}>Menu</Text></Pressable> : null}
    {snap.shift ? <Pressable accessibilityRole="button" accessibilityLabel="Open SOS" onPress={openSos} style={[styles.railButton, { backgroundColor: p.status.critical.bg }]}><Icon name="stop" color={p.status.critical.fg} size={18} /><Text style={[type.label, { color: p.status.critical.fg }]}>SOS</Text></Pressable> : null}
    <Pressable onLongPress={openPresenter} delayLongPress={3000}><Text style={[type.heading, { color: p.onPrimary }]}>{snap.local_time}</Text></Pressable>
    <Text style={[type.caption, { color: p.onPrimary }]}>{snap.shift?.operator.display_name ?? 'No operator'}</Text>
  </View>;
}

const styles = StyleSheet.create({
  flag: { minHeight: 36, flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', borderRadius: radius.flag, paddingHorizontal: space.sm, paddingVertical: space.xs, gap: space.sm },
  flagDetail: { paddingLeft: space.sm, borderLeftWidth: 1, borderLeftColor: 'rgba(255,255,255,0.45)' },
  source: { borderLeftWidth: 4, paddingLeft: space.sm, paddingVertical: 2, alignSelf: 'flex-start' },
  row: { minHeight: 72, flexDirection: 'row', alignItems: 'stretch', borderBottomWidth: 1 },
  rowFocused: { borderWidth: 3, borderRadius: radius.control },
  rowMarker: { width: 7, marginRight: space.md },
  group: { borderTopWidth: 1, marginBottom: space.xl },
  groupTitle: { paddingTop: space.md, marginBottom: space.md },
  workSurface: { flex: 1, width: '100%', overflow: 'hidden' },
  instrument: { flex: 1, padding: space.xl, justifyContent: 'center' },
  valueLine: { flexDirection: 'row', alignItems: 'flex-end', gap: space.sm },
  continuity: { width: 210, paddingVertical: space.md, paddingRight: space.xl },
  stop: { minHeight: 70, flexDirection: 'row', position: 'relative' },
  stopLine: { width: 8, marginLeft: 8, marginRight: space.lg },
  stopNode: { position: 'absolute', left: 2, top: 4, width: 20, height: 20, borderWidth: 4, borderRadius: 10 },
  screenTitle: { minHeight: 64, justifyContent: 'center', paddingHorizontal: space.xl, borderBottomWidth: 1 },
  screenBody: { width: '100%', paddingVertical: space.lg, gap: space.md },
  actionBar: { minHeight: 64, flexDirection: 'row', alignItems: 'center', paddingHorizontal: space.lg, gap: space.lg, flexWrap: 'wrap' },
  actions: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: space.lg, flexWrap: 'wrap' },
  actionPair: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  key: { minWidth: 30, textAlign: 'center', backgroundColor: '#FFFFFF', borderRadius: radius.control, paddingHorizontal: 6, paddingVertical: 2 },
  feedback: { flexDirection: 'row', alignItems: 'center', gap: space.sm, maxWidth: 440 },
  machineRail: { minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: space.lg, paddingHorizontal: space.lg, flexWrap: 'wrap' },
  machineSlot: { flexDirection: 'row', alignItems: 'center', gap: space.sm },
  machineState: { flexDirection: 'row', alignItems: 'center', gap: space.xs, paddingHorizontal: space.sm, paddingVertical: space.xs, borderRadius: radius.flag },
  railButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: space.xs, backgroundColor: '#FFFFFF', paddingHorizontal: space.md, borderRadius: radius.control },
});
