import { NextResponse } from 'next/server';
import { globalStorage } from '@/cartridges/asset-maintenance/adapters/in-memory-storage';

export async function POST() {
  try {
    globalStorage.reset();
    const assets = await globalStorage.assets.findAll();

    return NextResponse.json({
      success: true,
      message: 'Demonstration environment successfully reset to ground-truth seed fixtures',
      fleet_count: assets.length,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to reset demo state' },
      { status: 500 }
    );
  }
}
