// Shared cab UI components (technical spec §4.5, §7.1): every status is colour + icon + word; rows ≥ 64 dp;
// focus ring 4 dp plus a ▶ marker (never colour-only).
import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useHost } from '../engine/host';
import { day, night, type Palette, space, type StatusTone, type } from './tokens';

export function usePalette(): Palette {
  const local = useHost((s) => s.snapshot?.local_time);
  const hour = local ? Number(local.slice(0, 2)) : 12;
  return hour >= 19 || hour < 6 ? night : day;
}

const ICONS: Record<StatusTone, string> = { ok: '✔', info: 'ℹ', caution: '▲', warning: '⚠', critical: '⛔', unavailable: '⊘' };

export function StatusPill({ tone, word, detail }: { tone: StatusTone; word: string; detail?: string }) {
  const p = usePalette();
  const c = p.status[tone];
  return (
    <View style={[styles.pill, { backgroundColor: c.bg }]} accessibilityLabel={`${word}${detail ? `, ${detail}` : ''}`}>
      <Text style={[type.label, { color: c.fg }]}>{ICONS[tone]} {word}</Text>
      {detail ? <Text style={[type.caption, { color: c.fg, marginLeft: space.sm }]}>{detail}</Text> : null}
    </View>
  );
}

export function ProvenanceTag({ source }: { source: 'observed' | 'reported' | 'inferred' | 'reviewed' }) {
  const p = usePalette();
  const word = { observed: 'Observed', reported: 'Reported', inferred: 'Inferred', reviewed: 'Reviewed' }[source];
  return (
    <View style={[styles.tag, { backgroundColor: p.provenance[source] }]}>
      <Text style={[type.caption, { color: '#FFFFFF' }]}>{word}</Text>
    </View>
  );
}

export function Row({ focused, disabled, onPress, children }: { focused: boolean; disabled?: boolean; onPress?: () => void; children: ReactNode }) {
  const p = usePalette();
  return (
    <Pressable
      onPress={disabled ? undefined : onPress}
      style={[styles.row, { backgroundColor: focused ? p.surfaceAlt : p.surface, borderColor: focused ? p.focus : p.border,
        borderWidth: focused ? 4 : 1, opacity: disabled ? 0.55 : 1 }]}
      accessibilityState={{ selected: focused, disabled }}
    >
      <Text style={[type.heading, { color: p.focus, width: 28 }]}>{focused ? '▶' : ' '}</Text>
      <View style={{ flex: 1 }}>{children}</View>
    </Pressable>
  );
}

export function T({ children, style, muted, variant = 'body' }: { children: ReactNode; style?: object; muted?: boolean; variant?: keyof typeof type }) {
  const p = usePalette();
  return <Text style={[type[variant], { color: muted ? p.textMuted : p.text }, style]}>{children}</Text>;
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={{ marginBottom: space.lg }}>
      <T variant="label" muted style={{ marginBottom: space.sm, textTransform: 'uppercase' }}>{title}</T>
      {children}
    </View>
  );
}

export function Screen({ title, hints, children, scroll = true }: { title: string; hints: string; children: ReactNode; scroll?: boolean }) {
  const p = usePalette();
  const body = <View style={{ padding: space.lg, gap: space.sm }}>{children}</View>;
  return (
    <View style={{ flex: 1, backgroundColor: p.bg }}>
      <View style={{ paddingHorizontal: space.lg, paddingTop: space.md }}>
        <T variant="title">{title}</T>
      </View>
      {scroll ? <ScrollView style={{ flex: 1 }}>{body}</ScrollView> : <View style={{ flex: 1 }}>{body}</View>}
      <ActionBar hints={hints} />
    </View>
  );
}

export function ActionBar({ hints }: { hints: string }) {
  const p = usePalette();
  const msg = useHost((s) => s.lastMessage);
  return (
    <View style={[styles.actionBar, { backgroundColor: p.primaryBg }]}>
      <Text style={[type.label, { color: p.onPrimary, flex: 1 }]} numberOfLines={1}>{hints}</Text>
      {msg ? <Text style={[type.label, { color: p.onPrimary }]} numberOfLines={1}>⚠ {msg}</Text> : null}
    </View>
  );
}

export function AppStatusBar() {
  const p = usePalette();
  const snap = useHost((s) => s.snapshot);
  const openPresenter = () => useHost.setState((s) => ({ presenterOpen: !s.presenterOpen }));
  if (!snap) return null;
  const unavailable = snap.signal_health.filter((h) => !h.fresh).length;
  const stateTone: StatusTone = snap.machine.state === 'UNKNOWN' ? 'unavailable' : snap.machine.state === 'WORKING' || snap.machine.state === 'TRAVELLING' ? 'info' : 'ok';
  const initials = snap.shift?.operator.display_name.slice(0, 2).toUpperCase() ?? '—';
  return (
    <View style={[styles.statusBar, { backgroundColor: p.surface, borderColor: p.border }]}>
      <StatusPill tone="unavailable" word="Offline" detail="safety and tasks working, assistant limited" />
      <T variant="label">{snap.pending_sync} waiting</T>
      <StatusPill tone={unavailable ? 'unavailable' : 'ok'} word={unavailable ? `${unavailable} unavailable` : 'Sensors OK'} />
      <StatusPill tone={stateTone} word={snap.machine.state} />
      <View style={{ flex: 1 }} />
      <T variant="label">{snap.machine.machine_id}</T>
      <Pressable onLongPress={openPresenter} delayLongPress={3000} onPress={undefined}>
        <T variant="heading">{snap.local_time}</T>
      </Pressable>
      <T variant="label" muted>{initials}</T>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: { flexDirection: 'row', alignItems: 'center', borderRadius: 8, paddingHorizontal: space.md, paddingVertical: space.xs },
  tag: { borderRadius: 6, paddingHorizontal: space.sm, paddingVertical: 2, alignSelf: 'flex-start' },
  row: { minHeight: 64, flexDirection: 'row', alignItems: 'center', borderRadius: 10, paddingHorizontal: space.md, paddingVertical: space.sm },
  actionBar: { minHeight: 64, flexDirection: 'row', alignItems: 'center', paddingHorizontal: space.lg, gap: space.lg },
  statusBar: { minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: space.md, paddingHorizontal: space.lg, borderBottomWidth: 1, flexWrap: 'wrap' },
});
