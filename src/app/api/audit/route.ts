import { NextResponse } from 'next/server';
import { globalStorage } from '@/adapters/in-memory-storage';

export async function GET() {
  try {
    const audits = await globalStorage.audit.findAll();
    return NextResponse.json({
      success: true,
      count: audits.length,
      data: audits,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve compliance audit logs' },
      { status: 500 }
    );
  }
}
