// Shift Ledger (technical spec §5.3.1, product §7.1): append-only; corrections supersede, never edit.
import type { Audience, LedgerEntry, LedgerKind, Source } from '../types';

export interface LedgerStore {
  append(entry: LedgerEntry): void;
  all(): readonly LedgerEntry[];
}

/** In-memory store (slice 1). The SQLite adapter (T16) implements the same port. */
export class MemoryLedgerStore implements LedgerStore {
  private entries: LedgerEntry[] = [];
  append(entry: LedgerEntry): void {
    this.entries.push(entry);
  }
  all(): readonly LedgerEntry[] {
    return this.entries;
  }
}

/** Default audience per kind/subtype (§5.3.2). */
export function defaultAudience(kind: LedgerKind, subtype: string): Audience {
  if (kind === 'learning_event') return 'operator_only';
  if (kind === 'incident' || subtype === 'incident_report' || subtype === 'incident_extraction' || subtype === 'alert_feedback') return 'safety';
  if (kind === 'handover_item' || subtype === 'handover_note' || subtype === 'site_tip') return 'next_operator';
  if (subtype === 'help_request') return 'trainer';
  if (subtype === 'recommendation' || subtype === 'recommendation_feedback') return 'operator_only';
  return 'site';
}

/** Entries that are ever sent to the server (§6.2 push rules). */
export function syncsToServer(e: LedgerEntry): boolean {
  return e.audience !== 'operator_only' && e.kind !== 'learning_event';
}

export interface EntryInput {
  kind: LedgerKind;
  subtype: string;
  source: Source;
  payload: Record<string, unknown>;
  observed_at: number;
  audience?: Audience;
  rule_or_model_version?: string | null;
  confidence?: 'high' | 'medium' | 'low' | null;
  original_text?: string | null;
  supersedes?: string | null;
  freshness_s?: number | null;
}

export class Ledger {
  constructor(
    private readonly store: LedgerStore,
    private readonly ctx: { device_id: string; machine_id: string; data_origin: string; newId: () => string; now: () => number },
  ) {}

  append(input: EntryInput, shift_id: string | null, operator_id: string | null): LedgerEntry {
    const entry: LedgerEntry = {
      entry_id: this.ctx.newId(),
      device_id: this.ctx.device_id,
      shift_id,
      machine_id: this.ctx.machine_id,
      operator_id,
      kind: input.kind,
      subtype: input.subtype,
      source: input.source,
      payload: input.payload,
      observed_at: input.observed_at,
      recorded_at: this.ctx.now(),
      freshness_s: input.freshness_s ?? null,
      confidence: input.confidence ?? null,
      rule_or_model_version: input.rule_or_model_version ?? null,
      original_text: input.original_text ?? null,
      supersedes: input.supersedes ?? null,
      audience: input.audience ?? defaultAudience(input.kind, input.subtype),
      data_origin: this.ctx.data_origin,
      sync_status: 'pending',
      chain_seq: null,
      prev_hash: null,
      content_hash: null,
      canonical_payload: null,
    };
    if ((entry.kind === 'alert' || entry.kind === 'inference') && !entry.rule_or_model_version) {
      throw new Error(`rule_or_model_version is required for ${entry.kind}/${entry.subtype} (NFR-15)`);
    }
    this.store.append(entry);
    return entry;
  }

  all(): readonly LedgerEntry[] {
    return this.store.all();
  }

  /** Effective view: the newest correction replaces its target's payload; a null replacement retracts it. */
  current(): LedgerEntry[] {
    const entries = this.store.all();
    const latest = new Map<string, LedgerEntry>();
    for (const e of entries) {
      if (e.kind !== 'correction' || !e.supersedes) continue;
      let root = e.supersedes;
      const seen = new Set<string>();
      for (;;) {
        const parent = entries.find((x) => x.entry_id === root);
        if (!parent || parent.kind !== 'correction' || !parent.supersedes || seen.has(root)) break;
        seen.add(root);
        root = parent.supersedes;
      }
      const prev = latest.get(root);
      if (!prev || e.recorded_at > prev.recorded_at || (e.recorded_at === prev.recorded_at && e.entry_id > prev.entry_id)) {
        latest.set(root, e);
      }
    }
    const out: LedgerEntry[] = [];
    for (const e of entries) {
      if (e.kind === 'correction') continue;
      const fix = latest.get(e.entry_id);
      if (!fix) {
        out.push(e);
        continue;
      }
      const replacement = (fix.payload as { replacement?: Record<string, unknown> | null }).replacement;
      if (replacement === null || replacement === undefined) continue;          // retracted
      out.push({ ...e, payload: replacement, source: 'reported' });
    }
    return out;
  }

  history(entryId: string): LedgerEntry[] {
    return this.store.all().filter((e) => e.entry_id === entryId || e.supersedes === entryId);
  }
}
