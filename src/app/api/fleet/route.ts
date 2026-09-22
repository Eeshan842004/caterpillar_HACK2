import { NextResponse } from 'next/server';
import { globalStorage } from '@/cartridges/asset-maintenance/adapters/in-memory-storage';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const assets = await globalStorage.assets.findAll();
    return NextResponse.json({
      success: true,
      count: assets.length,
      data: assets,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve fleet equipment list' },
      { status: 500 }
    );
  }
}
