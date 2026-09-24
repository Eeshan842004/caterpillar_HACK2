// Alert manager, speech queue and alert-budget counters (technical spec §8.3, product §12).
import type { AlertLevel, AlertStatus, AlertType, ObjectType, Place } from '../types';

export interface AlertDetails {
  object_id?: string | null;
  object_type?: ObjectType | null;
  place?: Place | null;
  distance_m?: number | null;
  ttc_s?: number | null;
  multiplier?: number | null;
  zone_id?: string | null;
  speed_kmh?: number | null;
  limit_kmh?: number | null;
  safe_exit?: Record<string, unknown> | null;
  clear_reason?: string | null;
}

export interface Alert extends AlertDetails {
  alert_id: string;
  alert_type: AlertType;
  level: AlertLevel;
  status: AlertStatus;
  group_key: string;
  raised_at: number;
  acknowledged_at: number | null;
  cleared_at: number | null;
  last_spoken_at: number | null;
  occurrences: number;
}

export interface SpeechOut {
  id: string;
  text: string;
  priority: number; // 0 critical … 5 narration
  alert_id?: string;
  at: number;
}

export interface BudgetHour {
  window_start: number;
  operating_s: number;
  alerts_raised: number;
  critical_time_ms: number;
  repeats_spoken: number;
  repeats_suppressed_after_ack: number;
  duplicate_raises_prevented: number;
  noncritical_prompts_deferred: number;
  critical_delivery_ms: number[];
  acknowledged: number;
  resolved: number;
}

export type AlertEmit = (subtype: 'raised' | 'escalated' | 'acknowledged' | 'cleared', alert: Alert, source: 'observed' | 'reported') => void;

const LEVEL_RANK: Record<AlertLevel, number> = { INFO: 0, CAUTION: 1, WARNING: 2, ADVISORY: 2, CRITICAL: 3 };
const SPEECH_PRIORITY: Record<AlertLevel, number> = { CRITICAL: 0, WARNING: 1, ADVISORY: 1, CAUTION: 2, INFO: 3 };
const REPEAT_S: Partial<Record<AlertType, number>> = {
  'A-BELT-MOVE': 5,
  'A-BELT-OPER': 20,
  'A-PROX-CRIT': 3,
  'A-PROX-WARN': 8,
  'A-SPEED': 10,
};

const OBJECT_WORD: Record<ObjectType, string> = {
  person: 'Person', light_vehicle: 'Light vehicle', heavy_vehicle: 'Truck', structure: 'Structure', unknown: 'Object',
};

export function placeWords(place: Place | null | undefined): string {
  return (place ?? 'unknown').replace('_', ' ');
}

/** Spoken text (≤ 12 words, F11-R9) for an alert, from product §12. */
export function alertSpeech(a: Pick<Alert, 'alert_type' | 'object_type' | 'place' | 'speed_kmh' | 'limit_kmh'>, machineClass: string): string {
  switch (a.alert_type) {
    case 'A-BELT-MOVE': return 'Seatbelt. Machine moving.';
    case 'A-BELT-OPER': return 'Seatbelt. Machine operating.';
    case 'A-BELT-UNAV': return 'Belt monitoring unavailable.';
    case 'A-PROX-CAUT': return `${OBJECT_WORD[a.object_type ?? 'unknown']}, ${placeWords(a.place)}.`;
    case 'A-PROX-WARN': return `${OBJECT_WORD[a.object_type ?? 'unknown']} close, ${placeWords(a.place)}.`;
    case 'A-PROX-CRIT': return machineClass === 'haul_truck' ? 'Stop. Person in path.' : 'Stop. Person in swing area.';
    case 'A-PROX-UNAV': return 'Proximity monitoring unavailable.';
    case 'A-SPEED': return `Speed ${Math.round(a.speed_kmh ?? 0)}. Limit ${Math.round(a.limit_kmh ?? 0)}.`;
    case 'A-EXIT-UNSEC': return 'Secure the machine before exiting.';
    case 'A-IDLE-ASK': return 'Why the wait?';
    case 'A-HEAT': return 'High heat. Consider a water break.';
    case 'A-WIND': return 'Strong wind. Check load and boom.';
    case 'A-SOS': return 'SOS sent. Also call on radio.';
  }
}

export class AlertManager {
  readonly alerts = new Map<string, Alert>();
  private byGroup = new Map<string, string>();
  private lastSpoken: SpeechOut | null = null;
  readonly speech: SpeechOut[] = [];
  readonly budget: BudgetHour[] = [];
  private speechSeq = 0;

  constructor(
    private readonly newId: () => string,
    private readonly emit: AlertEmit,
    private readonly machineClass: string,
  ) {}

  private hour(now: number): BudgetHour {
    const start = Math.floor(now / 3_600_000) * 3_600_000;
    let h = this.budget[this.budget.length - 1];
    if (!h || h.window_start !== start) {
      h = {
        window_start: start, operating_s: 0, alerts_raised: 0, critical_time_ms: 0, repeats_spoken: 0,
        repeats_suppressed_after_ack: 0, duplicate_raises_prevented: 0, noncritical_prompts_deferred: 0,
        critical_delivery_ms: [], acknowledged: 0, resolved: 0,
      };
      this.budget.push(h);
      if (this.budget.length > 24) this.budget.shift();
    }
    return h;
  }

  countOperatingSecond(now: number): void {
    this.hour(now).operating_s += 1;
  }

  countDeferredPrompt(now: number): void {
    this.hour(now).noncritical_prompts_deferred += 1;
  }

  private speak(a: Alert, now: number): void {
    const out: SpeechOut = {
      id: `sp-${++this.speechSeq}`, text: alertSpeech(a, this.machineClass), priority: SPEECH_PRIORITY[a.level],
      alert_id: a.alert_id, at: now,
    };
    this.speech.push(out);
    this.lastSpoken = out;
    a.last_spoken_at = now;
    if (a.level === 'CRITICAL') this.hour(now).critical_delivery_ms.push(0); // app records wall-clock latency (NFR-02)
  }

  active(): Alert[] {
    return [...this.alerts.values()]
      .filter((a) => a.status === 'RAISED' || a.status === 'ACKNOWLEDGED')
      .sort((x, y) => LEVEL_RANK[y.level] - LEVEL_RANK[x.level] || y.raised_at - x.raised_at);
  }

  byGroupKey(group: string): Alert | undefined {
    const id = this.byGroup.get(group);
    return id ? this.alerts.get(id) : undefined;
  }

  raise(type: AlertType, level: AlertLevel, group: string, details: AlertDetails, now: number): Alert {
    const existing = this.byGroupKey(group);
    if (existing && (existing.status === 'RAISED' || existing.status === 'ACKNOWLEDGED')) {
      Object.assign(existing, details);
      if (LEVEL_RANK[level] > LEVEL_RANK[existing.level]) {
        existing.alert_type = type;
        existing.level = level;
        existing.status = 'RAISED';
        existing.acknowledged_at = null;
        this.emit('escalated', existing, 'observed');
        this.speak(existing, now);
      } else if (type !== existing.alert_type && LEVEL_RANK[level] < LEVEL_RANK[existing.level]) {
        // downgrade (e.g. MOVE → OPER) is modelled as clear + raise by the caller
        this.hour(now).duplicate_raises_prevented += 1;
      } else {
        this.hour(now).duplicate_raises_prevented += 1;
      }
      return existing;
    }
    const windowMs = 60_000;
    if (existing && existing.status === 'CLEARED' && existing.cleared_at !== null && now - existing.cleared_at <= windowMs) {
      const higher = LEVEL_RANK[level] > LEVEL_RANK[existing.level];
      Object.assign(existing, details, { alert_type: type, level, status: 'RAISED', cleared_at: null, acknowledged_at: null });
      existing.occurrences += 1;
      this.emit('raised', existing, 'observed');
      this.hour(now).alerts_raised += 1;
      if (higher || existing.last_spoken_at === null || now - existing.last_spoken_at > 10_000) this.speak(existing, now);
      return existing;
    }
    const alert: Alert = {
      alert_id: this.newId(), alert_type: type, level, status: 'RAISED', group_key: group, raised_at: now,
      acknowledged_at: null, cleared_at: null, last_spoken_at: null, occurrences: 1, ...details,
    };
    this.alerts.set(alert.alert_id, alert);
    this.byGroup.set(group, alert.alert_id);
    this.emit('raised', alert, 'observed');
    this.hour(now).alerts_raised += 1;
    this.speak(alert, now);
    return alert;
  }

  clear(group: string, reason: string, now: number): void {
    const a = this.byGroupKey(group);
    if (!a || (a.status !== 'RAISED' && a.status !== 'ACKNOWLEDGED')) return;
    a.status = 'CLEARED';
    a.cleared_at = now;
    a.clear_reason = reason;
    this.emit('cleared', a, 'observed');
    this.hour(now).resolved += 1;
  }

  clearWhere(predicate: (a: Alert) => boolean, reason: string, now: number): void {
    for (const a of this.active()) if (predicate(a)) this.clear(a.group_key, reason, now);
  }

  /** ACK: acknowledges the highest RAISED alert; with nothing to acknowledge it repeats the last alert (REPEAT_ALERT). */
  ack(now: number): Alert | null {
    const target = this.active().find((a) => a.status === 'RAISED' && a.alert_type !== 'A-EXIT-UNSEC');
    if (!target) {
      if (this.lastSpoken) this.speech.push({ ...this.lastSpoken, id: `sp-${++this.speechSeq}`, at: now });
      return null;
    }
    target.status = 'ACKNOWLEDGED';
    target.acknowledged_at = now;
    this.emit('acknowledged', target, 'reported');
    this.hour(now).acknowledged += 1;
    return target;
  }

  /** Acknowledge a specific alert (e.g. "Not exiting" on A-EXIT-UNSEC). */
  ackAlert(alert: Alert, now: number): void {
    if (alert.status !== 'RAISED') return;
    alert.status = 'ACKNOWLEDGED';
    alert.acknowledged_at = now;
    this.emit('acknowledged', alert, 'reported');
    this.hour(now).acknowledged += 1;
  }

  /** Repeat policy, checked every tick. Acknowledged alerts stay visible but are not repeated. */
  tickRepeats(now: number): void {
    for (const a of this.active()) {
      const every = REPEAT_S[a.alert_type];
      if (a.level === 'CRITICAL') this.hour(now).critical_time_ms += 1000;
      if (!every || a.last_spoken_at === null || now - a.last_spoken_at < every * 1000) continue;
      if (a.status === 'RAISED') {
        this.speak(a, now);
        this.hour(now).repeats_spoken += 1;
      } else {
        a.last_spoken_at = now;
        this.hour(now).repeats_suppressed_after_ack += 1;
      }
    }
  }

  drainSpeech(): SpeechOut[] {
    const out = this.speech.splice(0, this.speech.length);
    return out.sort((a, b) => a.priority - b.priority);
  }
}
