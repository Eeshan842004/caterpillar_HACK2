import { NextRequest, NextResponse } from 'next/server';
import { globalStorage } from '@/cartridges/asset-maintenance/adapters/in-memory-storage';
import { RecommendationEngine } from '@/cartridges/asset-maintenance/domain/services/recommendation-engine';

const engine = new RecommendationEngine();

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const assetId = params.id;
    const asset = await globalStorage.assets.findById(assetId);

    if (!asset) {
      return NextResponse.json(
        { success: false, error: `Asset with id ${assetId} not found` },
        { status: 404 }
      );
    }

    const faults = await globalStorage.faults.findActiveByAsset(assetId);
    const telemetry = await globalStorage.telemetry.findByAsset(assetId);
    const latestTelemetry = await globalStorage.telemetry.getLatestByAsset(assetId);

    const recommendation = engine.evaluate(asset, faults, latestTelemetry);

    return NextResponse.json({
      success: true,
      data: {
        asset,
        active_faults: faults,
        telemetry_history: telemetry,
        latest_telemetry: latestTelemetry,
        recommendation,
      },
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Internal server error evaluating asset health' },
      { status: 500 }
    );
  }
}
