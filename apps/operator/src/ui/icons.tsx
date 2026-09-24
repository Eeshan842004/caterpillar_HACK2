import { View } from 'react-native';
import type { StatusTone } from './tokens';

export type IconName = 'check' | 'info' | 'caution' | 'warning' | 'stop' | 'unavailable' | 'offline' | 'sensor' | 'machine' | 'clock' | 'task' | 'belt' | 'proximity' | 'idle';
export const TONE_ICON: Record<StatusTone, IconName> = { ok: 'check', info: 'info', caution: 'caution', warning: 'warning', critical: 'stop', unavailable: 'unavailable' };

/** Small platform-independent line icons. They deliberately avoid emoji/font glyph rendering. */
export function Icon({ name, color, size = 24 }: { name: IconName; color: string; size?: number }) {
  const stroke = Math.max(2, Math.round(size / 10));
  const round = name === 'check' || name === 'info' || name === 'clock' || name === 'sensor' || name === 'proximity' || name === 'idle';
  const stop = name === 'stop';
  return <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants" style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
    <View style={{ width: size - 2, height: size - 2, borderWidth: stroke, borderColor: color, borderRadius: round ? size : stop ? size / 4 : 2, transform: stop ? [{ rotate: '45deg' }] : undefined }} />
    {name === 'check' ? <><View style={{ position: 'absolute', width: size * .28, height: stroke, backgroundColor: color, left: size * .22, top: size * .54, transform: [{ rotate: '45deg' }] }} /><View style={{ position: 'absolute', width: size * .5, height: stroke, backgroundColor: color, left: size * .37, top: size * .46, transform: [{ rotate: '-48deg' }] }} /></> : null}
    {name === 'info' ? <><View style={{ position: 'absolute', width: stroke, height: size * .34, backgroundColor: color, top: size * .42 }} /><View style={{ position: 'absolute', width: stroke + 1, height: stroke + 1, borderRadius: stroke, backgroundColor: color, top: size * .23 }} /></> : null}
    {name === 'idle' ? <><View style={{ position: 'absolute', width: stroke, height: size * .4, backgroundColor: color, left: size * .35 }} /><View style={{ position: 'absolute', width: stroke, height: size * .4, backgroundColor: color, right: size * .35 }} /></> : null}
    {(name === 'caution' || name === 'warning' || name === 'stop' || name === 'unavailable') ? <View style={{ position: 'absolute', width: stroke, height: size * .48, backgroundColor: color }} /> : null}
    {(name === 'offline' || name === 'unavailable') ? <View style={{ position: 'absolute', width: size * .9, height: stroke, backgroundColor: color, transform: [{ rotate: '-45deg' }] }} /> : null}
    {(name === 'sensor' || name === 'proximity') ? <View style={{ position: 'absolute', width: size * .32, height: size * .32, borderRadius: size, backgroundColor: color }} /> : null}
  </View>;
}
