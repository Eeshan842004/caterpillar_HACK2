// Presenter / simulator panel (SD-06, D-06): opened with F2 or a 3 s press on the clock. Touch/mouse allowed
// because it is not an operator surface; it only drives the simulated machine (A-03).
import type { SignalName } from '@shiftmate/core';
import type { ReactNode } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { host, useHost } from '../engine/host';
import { useSync } from '../sync/client';
import { useKeys } from '../input/keys';
import { usePalette } from '../ui/components';
import { space, type } from '../ui/tokens';

function Btn({ label, onPress, active }: { label: string; onPress: () => void; active?: boolean }) {
  const p = usePalette();
  return (
    <Pressable onPress={() => { onPress(); host.flush(); }}
      style={[styles.btn, { backgroundColor: active ? p.focus : p.surfaceAlt, borderColor: p.border }]}>
      <Text style={[type.caption, { color: active ? '#FFFFFF' : p.text }]}>{label}</Text>
    </Pressable>
  );
}

function Group({ title, children }: { title: string; children: ReactNode }) {
  const p = usePalette();
  return (
    <View style={{ marginBottom: space.md }}>
      <Text style={[type.label, { color: p.textMuted, marginBottom: space.xs }]}>{title}</Text>
      <View style={styles.wrap}>{children}</View>
    </View>
  );
}

export function PresenterPanel() {
  const p = usePalette();
  const open = useHost((s) => s.presenterOpen);
  const speed = useHost((s) => s.speed);
  const snap = useHost((s) => s.snapshot);
  useKeys((k) => {
    if (k.action !== 'PRESENTER') return false;
    useHost.setState((s) => ({ presenterOpen: !s.presenterOpen }));
    return true;
  }, 300);
  const sim = host.sim;
  const offline = useSync((s) => s.simulatedOffline);
  if (!open || !sim || !snap) return null;
  const v = sim.state.values;
  const S = snap.machine.profile_id.startsWith('haul') ? 'park_brake' : 'hydraulic_lockout';
  const dropped = (n: SignalName) => sim.state.dropped.includes(n);
  const truck = snap.machine.machine_class === 'haul_truck';
  const person = (closing: number, bearing: number, dist: number) =>
    sim.addTrack({ type: 'person', bearing_deg: bearing, distance_m: dist, closing_mps: closing, quality: 0.9, seconds: 12 });

  return (
    <View style={[styles.panel, { backgroundColor: p.surface, borderColor: p.focus }]}>
      <ScrollView>
        <Text style={[type.heading, { color: p.text }]}>Presenter · simulated machine</Text>
        <Text style={[type.caption, { color: p.textMuted, marginBottom: space.md }]}>
          Signals and detections are simulated (A-03). F2 closes.
        </Text>
        <Group title="Machine">
          <Btn label="Engine off" onPress={() => sim.preset('off')} active={v.engine_on === false} />
          <Btn label={truck ? 'Park brake on' : 'Lockout on (secure)'} onPress={() => sim.preset('secured')} active={v.engine_on === true && v[S] === true} />
          <Btn label="Ready (released)" onPress={() => sim.preset('ready')} />
          {!truck ? <Btn label="Dig" onPress={() => sim.preset('dig')} active={v.implement_active === true} /> : null}
          <Btn label="Travel 12 km/h" onPress={() => sim.preset('travel_slow')} />
          <Btn label="Travel 42 km/h" onPress={() => sim.preset('travel_fast')} />
          <Btn label="+2 progress / +1 cycle" onPress={() => sim.addProgress(2)} />
        </Group>
        <Group title="Cab">
          <Btn label={v.seatbelt_fastened ? 'Belt: fastened' : 'Belt: OFF'} onPress={() => sim.toggle('seatbelt_fastened')} active={v.seatbelt_fastened === false} />
          <Btn label={v.cab_door_open ? 'Door: OPEN' : 'Door: closed'} onPress={() => sim.toggle('cab_door_open')} active={v.cab_door_open === true} />
          <Btn label={v.seat_occupied ? 'Seat: occupied' : 'Seat: VACANT'} onPress={() => sim.toggle('seat_occupied')} active={v.seat_occupied === false} />
          <Btn label={v.implement_neutral ? 'Implement: neutral' : 'Implement: raised'} onPress={() => sim.toggle('implement_neutral')} />
        </Group>
        <Group title="Proximity">
          <Btn label="Person approaching rear-left" onPress={() => person(1.2, 210, 11)} />
          <Btn label="Person departing rear" onPress={() => person(-1.0, 180, 7)} />
          <Btn label="Pickup crossing front" onPress={() => sim.addTrack({ type: 'light_vehicle', bearing_deg: 10, distance_m: 30, closing_mps: 4, quality: 0.9, seconds: 8 })} />
          <Btn label={sim.state.heartbeat_on ? 'Drop proximity feed' : 'Restore proximity feed'} onPress={() => sim.setHeartbeat(!sim.state.heartbeat_on)} active={!sim.state.heartbeat_on} />
        </Group>
        <Group title="Signals">
          <Btn label={dropped('seatbelt_fastened') ? 'Restore belt signal' : 'Drop belt signal'} onPress={() => sim.drop('seatbelt_fastened', !dropped('seatbelt_fastened'))} active={dropped('seatbelt_fastened')} />
          <Btn label={dropped('seat_occupied') ? 'Restore seat/door signals' : 'Drop seat/door signals'}
            onPress={() => { const d = !dropped('seat_occupied'); sim.drop('seat_occupied', d); sim.drop('cab_door_open', d); }} active={dropped('seat_occupied')} />
        </Group>
        <Group title="Conditions (operator report)">
          <Btn label={snap.conditions.rain ? 'Rain: ON' : 'Rain: off'} onPress={() => host.dispatch({ type: 'CONDITION_REPORT', condition: 'rain', active: !snap.conditions.rain })} active={snap.conditions.rain} />
          <Btn label={snap.conditions.dust ? 'Dust: ON' : 'Dust: off'} onPress={() => host.dispatch({ type: 'CONDITION_REPORT', condition: 'dust', active: !snap.conditions.dust })} active={snap.conditions.dust} />
          <Btn label={snap.conditions.darkness ? 'Dark: ON' : 'Dark: off'} onPress={() => host.dispatch({ type: 'CONDITION_REPORT', condition: 'darkness', active: !snap.conditions.darkness })} active={snap.conditions.darkness} />
        </Group>
        <Group title="Clock">
          {[1, 10, 60].map((s) => <Btn key={s} label={`${s}×`} onPress={() => host.setSpeed(s)} active={speed === s} />)}
          <Btn label="Fast-forward 5 min" onPress={() => host.fastForward(300)} />
          <Btn label="+1 min" onPress={() => host.fastForward(60)} />
        </Group>
        <Group title="Device">
          <Btn label={offline ? 'Restore signal' : 'Simulate no signal'} onPress={() => host.setSimulatedOffline(!offline)} active={offline} />
          <Btn label="Sync now" onPress={() => host.syncNow()} />
          <Btn label="Switch machine (demo only)" onPress={() => host.unpair()} />
        </Group>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  panel: { position: 'absolute', right: 0, top: 0, bottom: 0, width: 380, borderLeftWidth: 3, padding: space.lg, zIndex: 60 },
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: space.xs },
  btn: { paddingHorizontal: space.sm, paddingVertical: space.xs, borderRadius: 8, borderWidth: 1 },
});
