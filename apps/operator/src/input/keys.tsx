// No-touch input (technical spec §7.3, DR-06): keyboard + gamepad → actions, delivered to a handler stack so
// overlays (alert, Safe Exit Guard, prompt sheet, presenter) take keys before the screen underneath.
import { createContext, type ReactNode, useContext, useEffect, useRef } from 'react';
import { BackHandler, Platform } from 'react-native';

export type Action =
  | 'UP' | 'DOWN' | 'LEFT' | 'RIGHT' | 'OK' | 'BACK' | 'ACK' | 'PTT' | 'MENU' | 'PRESENTER' | 'SOS'
  | 'QUICK_1' | 'QUICK_2' | 'QUICK_3' | 'QUICK_4'
  | `DIGIT_${0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9}`;

const KEY_MAP: Record<string, Action> = {
  ArrowUp: 'UP', ArrowDown: 'DOWN', ArrowLeft: 'LEFT', ArrowRight: 'RIGHT', Enter: 'OK', NumpadEnter: 'OK',
  Escape: 'BACK', Backspace: 'BACK', '4': 'BACK', Space: 'ACK', KeyV: 'PTT', KeyM: 'MENU', Tab: 'MENU', F2: 'PRESENTER',
  KeyS: 'SOS', Digit1: 'QUICK_1', Digit2: 'QUICK_2', Digit3: 'QUICK_3', Digit4: 'QUICK_4', Numpad1: 'QUICK_1',
  Numpad2: 'QUICK_2', Numpad3: 'QUICK_3', Numpad4: 'QUICK_4',
  ButtonA: 'OK', ButtonB: 'BACK', ButtonX: 'QUICK_1', ButtonY: 'QUICK_2', ButtonL2: 'QUICK_3', ButtonR2: 'QUICK_4',
  ButtonL1: 'PTT', ButtonR1: 'ACK', ButtonStart: 'SOS', ButtonSelect: 'MENU',
};

/** Digit keys double as PIN digits on A1 (handlers receive both the quick action and the digit). */
function digitOf(key: string): number | null {
  const m = /^(?:Digit|Numpad)(\d)$/.exec(key);
  return m ? Number(m[1]) : null;
}

export interface KeyPress {
  action: Action | null;
  digit: number | null;
  key: string;
}

type Handler = (k: KeyPress) => boolean; // return true to consume

interface Registry {
  stack: { id: number; priority: number; handler: { current: Handler } }[];
  seq: number;
}

const Ctx = createContext<Registry>({ stack: [], seq: 0 });

function dispatchKey(reg: Registry, k: KeyPress): void {
  const ordered = [...reg.stack].sort((a, b) => b.priority - a.priority || b.id - a.id);
  for (const entry of ordered) if (entry.handler.current(k)) return;
}

export function KeyInputProvider({ children }: { children: ReactNode }) {
  const reg = useRef<Registry>({ stack: [], seq: 0 }).current;

  // Expo Go cannot load expo-key-event's native module. Keep browser keyboard
  // support and Android Back here; native hardware keys return in dev builds.
  useEffect(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const onKeyDown = (event: KeyboardEvent) => {
        if (event.repeat) return;
        const key = event.code || event.key;
        const action = KEY_MAP[key] ?? KEY_MAP[event.key] ?? null;
        if (action) event.preventDefault();
        dispatchKey(reg, { action, digit: digitOf(key), key });
      };
      window.addEventListener('keydown', onKeyDown);
      return () => window.removeEventListener('keydown', onKeyDown);
    }
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      dispatchKey(reg, { action: 'BACK', digit: null, key: 'hardwareBack' });
      return true;
    });
    return () => sub.remove();
  }, [reg]);

  // Web gamepad polling (standard mapping), edge-detected (§7.3)
  useEffect(() => {
    if (Platform.OS !== 'web' || typeof navigator === 'undefined' || !navigator.getGamepads) return;
    const names = ['ButtonA', 'ButtonB', 'ButtonX', 'ButtonY', 'ButtonL1', 'ButtonR1', 'ButtonL2', 'ButtonR2', 'ButtonSelect',
      'ButtonStart', '', '', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
    const prev: boolean[] = [];
    const id = setInterval(() => {
      const pad = navigator.getGamepads?.()[0];
      if (!pad) return;
      pad.buttons.forEach((b, i) => {
        const name = names[i];
        if (name && b.pressed && !prev[i]) dispatchKey(reg, { action: KEY_MAP[name] ?? null, digit: null, key: name });
        prev[i] = b.pressed;
      });
    }, 50);
    return () => clearInterval(id);
  }, [reg]);

  return <Ctx.Provider value={reg}>{children}</Ctx.Provider>;
}

/** Subscribe to keys while mounted. Higher priority = earlier (overlays use 100+, screens 0). */
export function useKeys(handler: Handler, priority = 0, enabled = true): void {
  const reg = useContext(Ctx);
  const ref = useRef(handler);
  ref.current = handler;
  useEffect(() => {
    if (!enabled) return;
    const entry = { id: ++reg.seq, priority, handler: ref };
    reg.stack.push(entry);
    return () => {
      const i = reg.stack.indexOf(entry);
      if (i >= 0) reg.stack.splice(i, 1);
    };
  }, [reg, priority, enabled]);
}
