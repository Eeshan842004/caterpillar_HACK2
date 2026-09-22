/**
 * Challenge-neutral evidence and audit contracts.
 *
 * Cartridges may add domain-specific fields, but should not redefine the
 * meaning of quality, evidence, provenance, or human-reviewed audit records.
 */

export type DataQualityState =
  | 'GOOD'
  | 'SUSPECT'
  | 'STALE'
  | 'MISSING'
  | 'OUT_OF_RANGE';

export interface EvidenceCitation<Value = number> {
  parameter: string;
  observed_value: Value;
  threshold_value?: Value;
  unit?: string;
  timestamp: string;
  source?: string;
  quality?: DataQualityState;
}

export interface AuditRecord<Action extends string = string> {
  id: string;
  timestamp: string;
  actor_name: string;
  actor_role: string;
  action: Action;
  target_id: string;
  details: string;
  payload_snapshot: Record<string, unknown>;
}

export interface EvidenceBackedDecision {
  confidence_score: number;
  evidence_citations: EvidenceCitation[];
  diagnostic_summary: string;
  recommended_action: string;
}
