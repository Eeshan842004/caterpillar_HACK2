/**
 * Public entry point for the asset-maintenance reference cartridge.
 *
 * The application imports the cartridge through this boundary so a revealed
 * challenge can replace it without presenting its domain as universal core.
 */
export { Workspace } from './components/Workspace';
export { RecommendationEngine } from './domain/services/recommendation-engine';
export { IngestionService } from './domain/services/ingestion';
export { OfflineSyncService } from './domain/services/offline-sync';
export { SafetyPolicyVerifier } from './domain/services/safety-policy';
export { InMemoryStorageContainer, globalStorage } from './adapters/in-memory-storage';
export * from './domain/types';
