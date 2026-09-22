import { WorkOrder, AuditEvent } from '../types';
import {
  ConsequentialActionPolicy,
  type PolicyValidationResult,
} from '@/core/safety/consequential-action-policy';

export type { PolicyValidationResult } from '@/core/safety/consequential-action-policy';

export class SafetyPolicyVerifier {
  constructor(private readonly corePolicy = new ConsequentialActionPolicy()) {}

  /**
   * Validates that consequential operational actions strictly satisfy ADR-0003 safety policies.
   */
  public validateWorkOrder(order: Partial<WorkOrder>): PolicyValidationResult {
    return this.corePolicy.validate({
      target_id: order.asset_id,
      title: order.title,
      approved_by: order.approved_by,
      approved_at: order.approved_at,
    });
  }

  /**
   * Generates a deterministic cryptographic checksum for an AuditEvent to guarantee tamper-evidence.
   */
  public generateAuditHash(event: Omit<AuditEvent, 'id'> & { id?: string }): string {
    return this.corePolicy.generateAuditHash(event);
  }

  /**
   * Verifies an audit record against an expected checksum.
   */
  public verifyAuditIntegrity(event: AuditEvent, expectedHash: string): boolean {
    return this.corePolicy.verifyAuditIntegrity(event, expectedHash);
  }
}
