// Global overlays: A7 alert overlay, A7E Safe Exit Guard, A8 prompt sheet, menu (technical spec §7.2).
import { alertSpeech } from '@shiftmate/core';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { host, useHost } from '../engine/host';
import { useKeys } from '../input/keys';
import { speak, stopSpeaking } from '../voice/speaker';
import { Row, StateFlag, T, usePalette } from './components';
import { Icon } from './icons';
import { levelTone, space, type } from './tokens';

export function AlertOverlay() {
  const p = usePalette();
  const snap = useHost((s) => s.snapshot);
  useKeys((k) => {
    if (k.action !== 'ACK') return false;
    host.dispatch({ type: 'ALERT_ACK' });            // ACK with nothing to acknowledge repeats the last alert
    return true;
  }, 50);
  if (!snap) return null;
  const active = snap.alerts.active.filter((a) => a.alert_type !== 'A-EXIT-UNSEC');
  const top = active[0];
  if (!top) return null;
  const machineClass = snap.machine.machine_class;
  const banner = top.level === 'CRITICAL' || top.level === 'WARNING';
  const tone = levelTone[top.level] ?? 'info';
  const c = p.status[tone];
  const word = top.level === 'CRITICAL' ? 'STOP' : top.level;
  if (banner) {
    return (
      <View style={[styles.banner, { backgroundColor: c.bg }]} accessibilityLiveRegion="assertive">
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.sm }}><Icon name={top.level === 'CRITICAL' ? 'stop' : 'warning'} color={c.fg} size={34} /><Text style={[type.title, { color: c.fg }]}>{word}</Text></View>
        <Text style={[type.heading, { color: c.fg, flex: 1, marginLeft: space.lg }]}>{alertSpeech(top, machineClass)}</Text>
        {top.status === 'ACKNOWLEDGED' ? <Text style={[type.label, { color: c.fg }]}>Acknowledged — hazard still active{active.length > 1 ? `  +${active.length - 1} more` : ''}</Text>
          : <Pressable onPress={() => host.dispatch({ type: 'ALERT_ACK' })} style={[styles.alertAction, { borderColor: c.fg }]}><Text style={[type.label, { color: c.fg }]}>Acknowledge</Text></Pressable>}
      </View>
    );
  }
  return (
    <View style={[styles.pills, { backgroundColor: p.surface }]}>
      {active.slice(0, 3).map((a) => (
        <StateFlag key={a.alert_id} tone={levelTone[a.level] ?? 'info'} word={a.level} detail={alertSpeech(a, machineClass)} />
      ))}
    </View>
  );
}

const CHECK_WORD = { confirmed: 'Confirmed', not_yet: 'Not yet', unavailable: 'Unavailable' } as const;
const CHECK_TONE = { confirmed: 'ok', not_yet: 'warning', unavailable: 'unavailable' } as const;

export function SafeExitOverlay() {
  const p = usePalette();
  const view = useHost((s) => s.snapshot?.safe_exit);
  const active = !!view?.active;
  useKeys((k) => {
    if (k.action === 'ACK') host.dispatch({ type: 'SAFE_EXIT_CANCEL' });   // ACK on A7E = "Not exiting"
    return true;                                                             // A7E takes every key (no menus behind it)
  }, 200, active);
  if (!view || !active) return null;
  const secureWord = view.secure_signal === 'park_brake' ? 'Parking brake engaged' : 'Hydraulic lockout engaged';
  const rows: [string, keyof typeof view.checklist][] = [
    ['Implement lowered / neutral', 'implement_neutral'], [secureWord, 'secure_signal'], ['Machine motion stopped', 'motion_stopped'],
  ];
  return (
    <View style={[StyleSheet.absoluteFill, { backgroundColor: p.status.warning.bg, padding: space.xxl, zIndex: 50 }]}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.lg }}><Icon name="warning" color={p.status.warning.fg} size={56} /><Text style={[type.display, { color: p.status.warning.fg, flex: 1 }]}>Secure the machine before exiting</Text></View>
      <View style={{ marginTop: space.xl, gap: space.md }}>
        {rows.map(([label, key]) => (
          <View key={key} style={[styles.checkRow, { backgroundColor: p.bg }]}>
            <Text style={[type.heading, { color: p.text, flex: 1 }]}>{label}</Text>
            <StateFlag tone={CHECK_TONE[view.checklist[key]]} word={CHECK_WORD[view.checklist[key]]} />
          </View>
        ))}
        <View style={[styles.checkRow, { backgroundColor: p.bg }]}>
          <Text style={[type.heading, { color: p.text, flex: 1 }]}>Exit only after the machine is secured</Text>
        </View>
      </View>
      {view.unavailable_signals.length ? (
        <Text style={[type.body, { color: p.status.warning.fg, marginTop: space.lg }]}>
          Unavailable: {view.unavailable_signals.join(', ')} — never treated as secured.
        </Text>
      ) : null}
      <View style={{ flex: 1 }} />
      <Text style={[type.heading, { color: p.status.warning.fg }]}>Advisory only — Throughline does not control the machine.</Text>
      <Pressable onPress={() => host.dispatch({ type: 'SAFE_EXIT_CANCEL' })} style={[styles.safeExitAction, { backgroundColor: p.bg }]}><Text style={[type.label, { color: p.text }]}>I am not exiting</Text></Pressable>
    </View>
  );
}

export function PromptSheet() {
  const p = usePalette();
  const prompt = useHost((s) => s.snapshot?.prompt ?? null);
  const [focus, setFocus] = useState(0);
  useKeys((k) => {
    if (!prompt) return false;
    const pick = (i: number) => {
      const opt = prompt.options[i];
      if (opt) host.dispatch({ type: 'PROMPT_ANSWER', prompt_id: prompt.prompt_id, option: opt.key });
      setFocus(0);
    };
    if (k.action?.startsWith('QUICK_')) {
      pick(Number(k.action.slice(6)) - 1);
      return true;
    }
    if (k.action === 'UP') setFocus((f) => Math.max(0, f - 1));
    else if (k.action === 'DOWN') setFocus((f) => Math.min(prompt.options.length - 1, f + 1));
    else if (k.action === 'OK') pick(focus);
    else if (k.action === 'BACK' && prompt.dismissible) host.dispatch({ type: 'PROMPT_DISMISS', prompt_id: prompt.prompt_id });
    else if (k.action === 'PTT') useHost.setState({ lastMessage: 'Voice is not in this build — use keys 1–4' });
    else return false;
    return true;
  }, 150, !!prompt);
  if (!prompt) return null;
  const secondsLeft = prompt.expires_at && useHost.getState().snapshot ? Math.max(0, Math.round((prompt.expires_at - (useHost.getState().snapshot?.now ?? 0)) / 1000)) : null;
  return (
    <View style={[styles.sheet, { backgroundColor: p.surface, borderColor: p.focus }]}>
      <T variant="title">{prompt.title}</T>
      {prompt.body ? <T muted>{prompt.body}</T> : null}
      <View style={{ gap: space.sm, marginTop: space.md }}>
        {prompt.options.map((o, i) => (
          <Row key={o.key} focused={i === focus} onPress={() => host.dispatch({ type: 'PROMPT_ANSWER', prompt_id: prompt.prompt_id, option: o.key })}>
            <T variant="heading">{i + 1}  {o.label}</T>
          </Row>
        ))}
      </View>
      <T variant="label" muted style={{ marginTop: space.md }}>
        Keys 1–{prompt.options.length}. OK chooses.{prompt.dismissible ? ' Back closes.' : ''}{secondsLeft !== null ? ` Closes in ${secondsLeft} s.` : ''}
      </T>
    </View>
  );
}

const MENU: { label: string; route: string | null; reason?: string }[] = [
  { label: 'Tasks', route: '/tasks' },
  { label: 'Briefing', route: '/briefing' },
  { label: 'Status & sync', route: '/status' },
  { label: 'Training', route: '/training' },
  { label: 'Shift summary', route: null, reason: 'Shift summary arrives in a later build (T26)' },
  { label: 'Handover & end shift', route: null, reason: 'Handover arrives in a later build (T29)' },
  { label: 'Log incident', route: null, reason: 'Incident reporting arrives in a later build (T25)' },
];

export function MenuOverlay() {
  const p = usePalette();
  const router = useRouter();
  const open = useHost((s) => s.menuOpen);
  const setOpen = (value: boolean | ((current: boolean) => boolean)) => useHost.setState((s) => ({ menuOpen: typeof value === 'function' ? value(s.menuOpen) : value }));
  const [focus, setFocus] = useState(0);
  const state = useHost((s) => s.snapshot?.machine.state);
  const signedIn = useHost((s) => !!s.snapshot?.shift);
  const operating = state === 'WORKING' || state === 'TRAVELLING' || state === 'UNKNOWN';
  useKeys((k) => {
    if (k.action === 'MENU' && signedIn) {
      if (operating) useHost.setState({ lastMessage: 'Menus locked while operating' });
      else setOpen((o) => !o);
      return true;
    }
    if (!open) return false;
    if (k.action === 'UP') setFocus((f) => Math.max(0, f - 1));
    else if (k.action === 'DOWN') setFocus((f) => Math.min(MENU.length - 1, f + 1));
    else if (k.action === 'BACK') setOpen(false);
    else if (k.action === 'OK') {
      const item = MENU[focus];
      if (item?.route) {
        setOpen(false);
        router.replace(item.route as never);
      } else if (item?.reason) useHost.setState({ lastMessage: item.reason });
    }
    return true;
  }, 120);
  if (!open || operating) return null;
  return (
    <View style={[styles.menu, { backgroundColor: p.surface, borderColor: p.border }]}>
      <T variant="title">Menu</T>
      {MENU.map((m, i) => (
        <Row key={m.label} focused={i === focus} disabled={!m.route} onPress={() => { if (m.route) { setOpen(false); router.replace(m.route as never); } }}>
          <T variant="heading">{m.label}</T>
          {m.reason ? <T variant="caption" muted>{m.reason}</T> : null}
        </Row>
      ))}
      <T variant="label" muted>Up/Down moves. OK opens. Back closes.</T>
    </View>
  );
}

export function VoiceOverlay() {
  const p = usePalette();
  const router = useRouter();
  const open = useHost((s) => s.voiceOpen);
  const snap = useHost((s) => s.snapshot);
  const [status, setStatus] = useState('Voice output ready');
  if (!open || !snap?.shift) return null;
  const next = snap.tasks.find((task) => task.is_next);
  const say = (text: string) => { setStatus(text); speak(text, 4); };
  const safety = `Safety status. Seatbelt ${snap.belt}. Proximity ${snap.proximity.status === 'clear' ? 'clear' : snap.proximity.status === 'unavailable' ? 'unavailable' : `${snap.proximity.level.toLowerCase()}, ${snap.proximity.object_type.replace('_', ' ')}, ${snap.proximity.place.replace('_', ' ')}`}.`;
  return <View style={[styles.voiceSheet, { backgroundColor: p.surface, borderColor: p.focus }]} accessibilityViewIsModal>
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.md }}><Icon name="info" color={p.focus} size={32} /><T variant="title" style={{ flex: 1 }}>Voice assistant</T><Pressable onPress={() => useHost.setState({ voiceOpen: false })} style={[styles.closeButton, { borderColor: p.border }]}><T variant="label">Close</T></Pressable></View>
    <StateFlag tone="info" word="Expo Go voice mode" detail="Spoken output and touch commands" />
    <T muted>Microphone recognition needs the native development build. Use these large touch commands in Expo Go.</T>
    <View style={{ gap: space.sm }}>
      <Row focused={false} onPress={() => say(next ? `Next task. ${next.task.task_type.replace('_', ' ')} at ${next.zone_name ?? next.task.location_text}.` : 'All tasks are complete.')}><T variant="heading">What’s next?</T></Row>
      <Row focused={false} onPress={() => say(safety)}><T variant="heading">Read safety status</T></Row>
      <Row focused={false} onPress={() => say(`You have ${snap.briefing.task_count} tasks today. ${snap.briefing.conditions_text}`)}><T variant="heading">Read shift briefing</T></Row>
      <Row focused={false} onPress={() => { stopSpeaking(); useHost.setState({ voiceOpen: false }); router.push('/training' as never); }}><T variant="heading">Open training</T></Row>
    </View>
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.md }}><T muted style={{ flex: 1 }}>{status}</T><Pressable onPress={() => { stopSpeaking(); setStatus('Voice stopped'); }} style={[styles.stopButton, { borderColor: p.border }]}><T variant="label">Stop voice</T></Pressable></View>
  </View>;
}

const styles = StyleSheet.create({
  banner: { minHeight: 120, flexDirection: 'row', alignItems: 'center', paddingHorizontal: space.xl, zIndex: 40 },
  pills: { flexDirection: 'row', gap: space.sm, padding: space.sm, flexWrap: 'wrap' },
  sheet: { position: 'absolute', left: space.lg, right: space.lg, bottom: 80, borderWidth: 3, borderRadius: 8, padding: space.xl, zIndex: 45 },
  checkRow: { minHeight: 72, flexDirection: 'row', alignItems: 'center', padding: space.lg, borderBottomWidth: 1 },
  menu: { position: 'absolute', top: 80, left: space.xl, width: 460, borderWidth: 2, borderRadius: 8, padding: space.lg, gap: space.sm, zIndex: 44 },
  voiceSheet: { position: 'absolute', top: space.lg, left: space.lg, right: space.lg, maxWidth: 680, alignSelf: 'center', borderWidth: 3, borderRadius: 8, padding: space.xl, gap: space.md, zIndex: 46 },
  alertAction: { minHeight: 52, justifyContent: 'center', paddingHorizontal: space.lg, borderWidth: 2, borderRadius: 4 },
  safeExitAction: { minHeight: 64, alignSelf: 'flex-start', justifyContent: 'center', paddingHorizontal: space.xl, borderRadius: 4, marginTop: space.md },
  closeButton: { minHeight: 48, justifyContent: 'center', paddingHorizontal: space.md, borderWidth: 2, borderRadius: 4 },
  stopButton: { minHeight: 52, justifyContent: 'center', paddingHorizontal: space.lg, borderWidth: 2, borderRadius: 4 },
});
