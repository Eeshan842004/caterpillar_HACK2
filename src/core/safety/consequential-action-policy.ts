import { createHash } from 'crypto';
import type { AuditRecord } from '../evidence/types';

export interface ConsequentialAction {
  target_id?: string;
  title?: string;
  approved_by?: string;
  approved_at?: string;
}

export interface PolicyValidationResult {
  isValid: boolean;
  violations: string[];
}

function canonicalize(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }

  if (value && typeof value === 'object') {
    return Object.keys(value as Record<string, unknown>)
      .sort()
      .reduce<Record<string, unknown>>((result, key) => {
        result[key] = canonicalize((value as Record<string, unknown>)[key]);
        return result;
      }, {});
  }

  return value;
}

/**
 * Reusable safety boundary for any challenge that turns a recommendation into
 * a consequential human-approved action.
 */
export class ConsequentialActionPolicy {
  public validate(action: ConsequentialAction): PolicyValidationResult {
    const violations: string[] = [];

    if (!action.approved_by?.trim()) {
      violations.push(
        'ADR-0003 Violation: Consequential actions require an explicit human approver signature.'
      );
    }

    if (!action.approved_at) {
      violations.push('Audit Violation: Approval timestamp is missing.');
    }

    if (!action.target_id) {
      violations.push('Data Integrity Violation: Target ID is required.');
    }

    if (!action.title?.trim()) {
      violations.push('Specification Violation: Action title cannot be empty.');
    }

    return { isValid: violations.length === 0, violations };
  }

  public generateAuditHash<Action extends string>(
    event: Omit<AuditRecord<Action>, 'id'> & { id?: string }
  ): string {
    const canonicalPayload = JSON.stringify(
      canonicalize({
        actor: event.actor_name,
        role: event.actor_role,
        action: event.action,
        target: event.target_id,
        timestamp: event.timestamp,
        details: event.details,
        snapshot: event.payload_snapshot,
      })
    );

    return createHash('sha256').update(canonicalPayload).digest('hex');
  }

  public verifyAuditIntegrity<Action extends string>(
    event: AuditRecord<Action>,
    expectedHash: string
  ): boolean {
    return this.generateAuditHash(event) === expectedHash;
  }
}
