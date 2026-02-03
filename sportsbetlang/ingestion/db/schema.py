"""SQL schema definitions for ingestion tables."""

TEAM_TABLE = """
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    league TEXT,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
"""

PLAYER_TABLE = """
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team_id TEXT,
    league TEXT,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
"""

GAMES_TABLE = """
CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    league TEXT,
    sport TEXT,
    start_time TIMESTAMPTZ,
    home_team_id TEXT,
    away_team_id TEXT,
    source TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
"""

ODDS_TABLE = """
CREATE TABLE IF NOT EXISTS odds_snapshots (
    event_id TEXT NOT NULL,
    book TEXT NOT NULL,
    market TEXT NOT NULL,
    selection TEXT NOT NULL,
    line DOUBLE PRECISION,
    price DOUBLE PRECISION NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    raw JSONB,
    PRIMARY KEY (book, market, selection, event_id, observed_at)
);
"""

INJURIES_TABLE = """
CREATE TABLE IF NOT EXISTS injury_reports (
    player_id TEXT,
    team_id TEXT,
    league TEXT,
    status TEXT,
    injury_type TEXT,
    body_part TEXT,
    minutes_restriction TEXT,
    source TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    effective_date DATE,
    confidence DOUBLE PRECISION NOT NULL,
    raw_text TEXT,
    raw JSONB,
    PRIMARY KEY (player_id, observed_at, source)
);
"""

FEATURES_GAME_TEAM_TABLE = """
CREATE TABLE IF NOT EXISTS features_game_team (
    game_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    rest_days INTEGER,
    back_to_back BOOLEAN,
    rolling_efficiency DOUBLE PRECISION,
    closing_line DOUBLE PRECISION,
    line_movement DOUBLE PRECISION,
    injury_impact BOOLEAN,
    PRIMARY KEY (game_id, team_id, observed_at)
);
"""

FEATURES_GAME_PLAYER_TABLE = """
CREATE TABLE IF NOT EXISTS features_game_player (
    game_id TEXT NOT NULL,
    player_id TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    minutes_restriction BOOLEAN,
    injury_status TEXT,
    rolling_usage DOUBLE PRECISION,
    PRIMARY KEY (game_id, player_id, observed_at)
);
"""

SCHEMA_STATEMENTS = [
    TEAM_TABLE,
    PLAYER_TABLE,
    GAMES_TABLE,
    ODDS_TABLE,
    INJURIES_TABLE,
    FEATURES_GAME_TEAM_TABLE,
    FEATURES_GAME_PLAYER_TABLE,
]
