# SportsBetLang Ingestion Pipeline

This package provides a modular data ingestion and feature pipeline for sports betting models. It is designed to work with external tool adapters (odds, game data, injuries, database, and schema validation tools).

## Modules
- `sources/`: Tool-backed fetchers for odds, game data, and injuries.
- `extractors/`: LLM-to-JSON or rule-based extractors for messy text.
- `normalizers/`: Market normalization and entity resolution helpers.
- `db/`: Database client adapter and SQL schema definitions.
- `features/`: Feature engineering for team/game/player features.
- `pipelines/`: Pipeline runner and CLI entry points.

## Running the CLI
The CLI expects you to pass tool implementations through the host environment; the example below shows the command interface.

### Backfill mode
```bash
python -m sportsbetlang.ingestion.pipelines.cli backfill --sport nba --start 2025-10-01 --end 2025-10-31
```

### Live mode
```bash
python -m sportsbetlang.ingestion.pipelines.cli live --sport nba --start 2025-10-01 --end 2025-10-01 --markets spread,total,moneyline
```

## Entity Resolution Strategy
Stable IDs are created deterministically by hashing the normalized name + league (for teams) and name + team_id (for players). This avoids accidental merges across sources unless the source data includes matching identifiers.

## Schema Validation
JSON Schema definitions live in `schemas/`. The pipeline validates tool outputs using the provided `validate_schema` tool when available and falls back to a minimal local validator for required fields and types.
