from pathlib import Path

# Paths relative to the monorepo root
SERVER_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = SERVER_DIR.parent

DATA_DIR = ROOT_DIR / "data"
GENERATOR_DIR = DATA_DIR / "generator"
GENERATED_DIR = DATA_DIR / "generated"
CONFIG_PATH = GENERATOR_DIR / "config.yaml"

CONTENT_DIR = ROOT_DIR / "packages" / "content"
PROFILES_DIR = CONTENT_DIR / "profiles"
SEED_DIR = CONTENT_DIR / "seed"
SEED_PATH = SEED_DIR / "demo_seed.json"
DEMO_HISTORY_PATH = SEED_DIR / "demo_history.json"

DOCS_DIR = ROOT_DIR / "docs"
ASSUMPTIONS_PATH = DOCS_DIR / "GENERATOR_ASSUMPTIONS.md"
MODELS_DIR = CONTENT_DIR / "models"
PARITY_DIR = MODELS_DIR / "parity"
EVAL_RESULTS_DIR = ROOT_DIR / "eval" / "results"
