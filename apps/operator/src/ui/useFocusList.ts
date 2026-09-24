// Up/Down focus within a screen's list; OK activates the focused row (§7.3 focus manager, simplified per screen).
import { useEffect, useState } from 'react';
import { useKeys, type KeyPress } from '../input/keys';

export function useFocusList(count: number, onActivate: (index: number) => void, extra?: (k: KeyPress, index: number) => boolean) {
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (index >= count && count > 0) setIndex(count - 1);
  }, [count, index]);
  useKeys((k) => {
    if (k.action === 'UP') {
      setIndex((i) => Math.max(0, i - 1));
      return true;
    }
    if (k.action === 'DOWN') {
      setIndex((i) => Math.min(Math.max(0, count - 1), i + 1));
      return true;
    }
    if (k.action === 'OK' && count > 0) {
      onActivate(index);
      return true;
    }
    return extra ? extra(k, index) : false;
  });
  return [index, setIndex] as const;
}
