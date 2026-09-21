import { createHash } from 'crypto';
import { WorkOrder, AuditEvent } from '../types';

export interface PolicyValidationResult {
  isValid: boolean;
  violations: string[];
}

export class SafetyPolicyVerifier {
  /**
   * Validates that consequential operational actions strictly satisfy ADR-0003 safety policies.
   */
  public validateWorkOrder(order: Partial<WorkOrder>): PolicyValidationResult {
    const violations: string[] = [];

    if (!order.approved_by || order.approved_by.trim().length === 0) {
      violations.push('ADR-0003 Violation: Consequential work orders require an explicit human approver signature.');
    }

    if (!order.approved_at) {
      violations.push('Audit Violation: Approval timestamp is missing.');
    }

    if (!order.asset_id) {
      violations.push('Data Integrity Violation: Target asset ID is required.');
    }

    if (!order.title || order.title.trim().length === 0) {
      violations.push('Specification Violation: Work order title cannot be empty.');
    }

    return {
      isValid: violations.length === 0,
      violations,
    };
  }

  /**
   * Generates a deterministic cryptographic checksum for an AuditEvent to guarantee tamper-evidence.
   */
  public generateAuditHash(event: Omit<AuditEvent, 'id'> & { id?: string }): string {
    const canonicalPayload = JSON.stringify({
      actor: event.actor_name,
      role: event.actor_role,
      action: event.action,
      target: event.target_id,
      timestamp: event.timestamp,
      details: event.details,
      snapshot: event.payload_snapshot,
    });

    return createHash('sha256').update(canonicalPayload).digest('hex');
  }

  /**
   * Verifies an audit record against an expected checksum.
   */
  public verifyAuditIntegrity(event: AuditEvent, expectedHash: string): boolean {
    const computed = this.generateAuditHash(event);
    return computed === expectedHash;
  }
}
