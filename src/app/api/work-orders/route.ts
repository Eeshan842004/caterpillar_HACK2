import { NextRequest, NextResponse } from 'next/server';
import { globalStorage } from '@/adapters/in-memory-storage';
import { SafetyPolicyVerifier } from '@/domain/services/safety-policy';

const safetyVerifier = new SafetyPolicyVerifier();

export async function GET() {
  try {
    const orders = await globalStorage.workOrders.findAll();
    return NextResponse.json({
      success: true,
      count: orders.length,
      data: orders,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve work orders' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const orderPayload = {
      ...body,
      approved_at: body.approved_at || (body.approved_by ? new Date().toISOString() : undefined),
    };

    // Safety policy validation (ADR-0003)
    const policyResult = safetyVerifier.validateWorkOrder(orderPayload);
    if (!policyResult.isValid) {
      return NextResponse.json(
        {
          success: false,
          error: 'Safety Policy Gate Failure',
          violations: policyResult.violations,
        },
        { status: 400 }
      );
    }

    // Create Work Order
    const createdOrder = await globalStorage.workOrders.create({
      asset_id: body.asset_id,
      recommendation_id: body.recommendation_id || 'rec_direct',
      title: body.title,
      description: body.description || '',
      priority: body.priority || 'MEDIUM',
      status: 'DISPATCHED',
      assigned_technician: body.assigned_technician || 'Unassigned Field Tech',
      approved_by: body.approved_by,
      notes: body.notes,
    });

    // Record Immutable Audit Event with Hash
    const auditPayload = {
      actor_name: body.approved_by,
      actor_role: 'Authorized Supervisor',
      action: 'WORK_ORDER_DISPATCHED' as const,
      target_id: createdOrder.id,
      timestamp: new Date().toISOString(),
      details: `Work order dispatched: ${createdOrder.title}`,
      payload_snapshot: {
        asset_id: createdOrder.asset_id,
        priority: createdOrder.priority,
        technician: createdOrder.assigned_technician,
      },
    };

    const checksum = safetyVerifier.generateAuditHash(auditPayload);

    await globalStorage.audit.record({
      ...auditPayload,
      details: `${auditPayload.details} [SHA-256: ${checksum.substring(0, 12)}...]`,
    });

    return NextResponse.json(
      {
        success: true,
        data: createdOrder,
        audit_checksum: checksum,
      },
      { status: 201 }
    );
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to process work order dispatch' },
      { status: 500 }
    );
  }
}
