# Sports Betting Data Storage Guide

Comprehensive guide to storing and managing sports betting data in SportsBetLang.

## Table of Contents

1. [Overview](#overview)
2. [Sports Data Manager](#sports-data-manager)
3. [Data Models](#data-models)
4. [Import/Export Tools](#importexport-tools)
5. [Usage Examples](#usage-examples)
6. [Best Practices](#best-practices)

## Overview

SportsBetLang provides a comprehensive data storage system built on SQLite with enhanced schemas for:
- **Teams**: Team information with ratings and records
- **Games**: Game schedules, results, and betting lines
- **Odds Snapshots**: Historical odds tracking across multiple sportsbooks
- **Betting Records**: Complete bet tracking with CLV (Closing Line Value) analysis
- **Team Statistics**: Seasonal performance metrics

### Key Features

- **SQLite Database**: Fast, reliable local storage
- **Comprehensive Schema**: Tables for teams, games, odds, bets, and stats
- **Data Models**: Type-safe Python dataclasses for all entities
- **Import/Export**: CSV and JSON support for bulk operations
- **Advanced Querying**: Filter by sport, date, result, and more
- **Statistics**: Automatic calculation of win rates, ROI, units, etc.

## Sports Data Manager

The `SportsDataManager` class provides a unified interface for all data operations.

### Initialization

```python
from lib.sports_data_manager import SportsDataManager

# Create manager with default database
manager = SportsDataManager("sportsdata.db")

# Use in context (auto-closes)
with SportsDataManager("sportsdata.db") as manager:
    # Your code here
    pass
```

### Database Schema

The manager creates the following tables:

1. **teams**
   - id, name, sport, league, conference, division
   - elo_rating, home_record, away_record
   - created_at

2. **games**
   - id, sport, league, date, season, week
   - home_team, away_team, home_score, away_score
   - home_odds, away_odds, spread, total
   - completed, overtime, playoff
   - created_at

3. **odds_snapshots**
   - id, game_id, sportsbook, timestamp
   - home_moneyline, away_moneyline
   - spread_line, spread_odds_home, spread_odds_away
   - total_line, over_odds, under_odds
   - created_at

4. **bets**
   - id, game_id, date, sport, league
   - description, bet_type, selection
   - odds, stake, opening_odds, closing_odds, clv
   - result, profit, units
   - sportsbook, notes
   - created_at, settled_at

5. **team_stats**
   - id, team_id, season
   - games_played, wins, losses, ties
   - points_for, points_against
   - home_wins/losses, away_wins/losses
   - streak, last_updated

## Data Models

### Team

```python
from lib.sports_data_manager import Team

team = Team(
    name="Kansas City Chiefs",
    sport="nfl",
    league="NFL",
    conference="AFC",
    division="West",
    elo_rating=1650.0,
    home_record="8-1",
    away_record="7-2"
)
```

### Game

```python
from lib.sports_data_manager import Game

game = Game(
    sport="nfl",
    league="NFL",
    date="2024-01-15",
    season="2023",
    week=18,
    home_team="Kansas City Chiefs",
    away_team="Buffalo Bills",
    home_score=27,
    away_score=24,
    spread=-3.5,
    total=47.5,
    completed=True,
    overtime=False,
    playoff=True
)
```

### OddsSnapshot

```python
from lib.sports_data_manager import OddsSnapshot
from datetime import datetime

odds = OddsSnapshot(
    game_id=1,
    sportsbook="DraftKings",
    timestamp=datetime.now().isoformat(),
    home_moneyline=-175,
    away_moneyline=+150,
    spread_line=-3.5,
    spread_odds_home=-110,
    spread_odds_away=-110,
    total_line=47.5,
    over_odds=-110,
    under_odds=-110
)
```

### BettingRecord

```python
from lib.sports_data_manager import BettingRecord

bet = BettingRecord(
    game_id=1,
    date="2024-01-15",
    sport="nfl",
    league="NFL",
    description="Chiefs -3.5",
    bet_type="spread",  # spread, moneyline, total, prop
    selection="Kansas City Chiefs",
    odds=-110,
    stake=110.0,
    opening_odds=-105,
    closing_odds=-115,
    clv=5.0,  # Closing line value %
    result="win",  # win, loss, push
    profit=100.0,
    units=1.0,
    sportsbook="DraftKings",
    notes="Divisional playoff game"
)
```

## Import/Export Tools

### Command-Line Tool

The `data_import_export.py` tool provides bulk operations:

```bash
# Import games from CSV
python3 tools/data_import_export.py import-games \
  --input data/nfl_games.csv \
  --format csv

# Import bets from CSV
python3 tools/data_import_export.py import-bets \
  --input my_bets.csv

# Export games to JSON
python3 tools/data_import_export.py export-games \
  --output games_export.json \
  --format json \
  --sport nfl \
  --start-date 2024-01-01 \
  --end-date 2024-12-31

# Export betting statistics
python3 tools/data_import_export.py export-stats \
  --output stats_report.json

# Bulk import from directory
python3 tools/data_import_export.py bulk-import \
  --directory ./import_data/ \
  --format csv

# Generate sample data for testing
python3 tools/data_import_export.py generate-sample \
  --num-games 50
```

### CSV Format Requirements

#### Games CSV

Required columns:
- `date`: YYYY-MM-DD format
- `home_team`: Home team name
- `away_team`: Away team name

Optional columns:
- `home_score`, `away_score`: Final scores
- `season`: Season identifier
- `week`: Week number
- `spread`, `total`: Betting lines
- `overtime`, `playoff`: Boolean flags

#### Bets CSV

Required columns:
- `date`: YYYY-MM-DD format
- `sport`: Sport code (nfl, nba, mlb, etc.)
- `bet_type`: spread, moneyline, total, or prop
- `selection`: What was bet on
- `odds`: American odds format
- `stake`: Amount wagered

Optional columns:
- `game_id`: Link to games table
- `league`: League name
- `description`: Bet description
- `result`: win, loss, push
- `profit`: Net profit/loss
- `sportsbook`: Book name
- `notes`: Additional notes

## Usage Examples

### Team Management

```python
from lib.sports_data_manager import SportsDataManager, Team

manager = SportsDataManager()

# Add a team
chiefs = Team(
    name="Kansas City Chiefs",
    sport="nfl",
    league="NFL",
    conference="AFC",
    division="West",
    elo_rating=1650.0
)
team_id = manager.add_team(chiefs)

# Get a team
team = manager.get_team("Kansas City Chiefs", "nfl", "NFL")
print(f"Elo Rating: {team.elo_rating}")

# List all NFL teams
nfl_teams = manager.list_teams(sport="nfl")
for team in nfl_teams:
    print(f"{team.name}: {team.elo_rating}")
```

### Game Management

```python
from lib.sports_data_manager import Game

# Add a game
game = Game(
    sport="nfl",
    league="NFL",
    date="2024-01-15",
    season="2023",
    week=18,
    home_team="Kansas City Chiefs",
    away_team="Buffalo Bills",
    spread=-3.5,
    total=47.5
)
game_id = manager.add_game(game)

# Update with final score
manager.update_game_result(
    game_id=game_id,
    home_score=27,
    away_score=24,
    overtime=False
)

# List upcoming games
upcoming = manager.list_games(
    sport="nfl",
    completed=False,
    limit=10
)

# List games by date range
january_games = manager.list_games(
    sport="nfl",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### Odds Tracking

```python
from lib.sports_data_manager import OddsSnapshot
from datetime import datetime

# Add opening odds
opening_odds = OddsSnapshot(
    game_id=game_id,
    sportsbook="DraftKings",
    timestamp=datetime.now().isoformat(),
    home_moneyline=-165,
    away_moneyline=+145,
    spread_line=-3.5,
    spread_odds_home=-110,
    spread_odds_away=-110
)
manager.add_odds_snapshot(opening_odds)

# Add closing odds (later)
closing_odds = OddsSnapshot(
    game_id=game_id,
    sportsbook="DraftKings",
    timestamp=datetime.now().isoformat(),
    home_moneyline=-175,  # Line moved
    away_moneyline=+150,
    spread_line=-3.5,
    spread_odds_home=-115,  # Juice increased
    spread_odds_away=-105
)
manager.add_odds_snapshot(closing_odds)

# Get odds history
history = manager.get_odds_history(game_id)
for odds in history:
    print(f"{odds.timestamp}: Spread {odds.spread_line} ({odds.spread_odds_home})")

# Get closing odds
closing = manager.get_closing_odds(game_id)
print(f"Closing line: {closing.spread_line}")
```

### Bet Tracking

```python
from lib.sports_data_manager import BettingRecord

# Add a bet
bet = BettingRecord(
    game_id=game_id,
    date="2024-01-15",
    sport="nfl",
    league="NFL",
    description="Chiefs -3.5",
    bet_type="spread",
    selection="Kansas City Chiefs",
    odds=-110,
    stake=110.0,
    opening_odds=-105,
    closing_odds=-115,
    clv=5.0,  # Beat closing line by 5%
    sportsbook="DraftKings"
)
bet_id = manager.add_bet(bet)

# Settle bet after game
manager.settle_bet(
    bet_id=bet_id,
    result="win",
    profit=100.0
)

# List bets with filters
nfl_bets = manager.list_bets(sport="nfl", limit=50)
winning_bets = manager.list_bets(result="win")
recent_bets = manager.list_bets(
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

### Statistics and Analysis

```python
# Get overall betting stats
stats = manager.get_betting_stats()
print(f"Total Bets: {stats['total_bets']}")
print(f"Win Rate: {stats['win_rate']:.1f}%")
print(f"ROI: {stats['roi']:.1f}%")
print(f"Total Profit: ${stats['total_profit']:.2f}")
print(f"Units Won: {stats['units_won']:.2f}")

# Get stats by sport
nfl_stats = manager.get_betting_stats(sport="nfl")
nba_stats = manager.get_betting_stats(sport="nba")

# Get stats by bet type
spread_stats = manager.get_betting_stats(bet_type="spread")
ml_stats = manager.get_betting_stats(bet_type="moneyline")
total_stats = manager.get_betting_stats(bet_type="total")

# Compare performance
print("\nPerformance by Sport:")
for sport in ['nfl', 'nba', 'mlb', 'nhl']:
    stats = manager.get_betting_stats(sport=sport)
    if stats['total_bets'] > 0:
        print(f"{sport.upper()}: {stats['win_rate']:.1f}% win rate, "
              f"{stats['roi']:.1f}% ROI ({stats['total_bets']} bets)")
```

### Data Export

```python
# Export games to CSV
count = manager.export_games_to_csv(
    "nfl_games_2024.csv",
    sport="nfl",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
print(f"Exported {count} games")

# Export bets to CSV
count = manager.export_bets_to_csv("my_bets.csv", sport="nfl")
print(f"Exported {count} bets")

# Use import/export tool for JSON
from tools.data_import_export import DataImportExport

exporter = DataImportExport()
count = exporter.export_games_json(
    "games_export.json",
    sport="nfl",
    start_date="2024-01-01"
)

# Export comprehensive stats
stats = exporter.export_stats_json("betting_report.json")
```

## Best Practices

### 1. Consistent Data Entry

Always use consistent naming for teams and leagues:

```python
# Good - consistent naming
team1 = Team(name="Kansas City Chiefs", sport="nfl", league="NFL")
team2 = Team(name="Kansas City Chiefs", sport="nfl", league="NFL")

# Bad - inconsistent naming
team1 = Team(name="KC Chiefs", sport="nfl", league="NFL")
team2 = Team(name="Kansas City Chiefs", sport="NFL", league="nfl")
```

### 2. Track Opening and Closing Lines

Always record both opening and closing odds for CLV analysis:

```python
bet = BettingRecord(
    # ... other fields ...
    odds=-110,  # Your bet odds
    opening_odds=-105,  # When line first posted
    closing_odds=-115,  # Final line before game
    clv=5.0  # You beat closing by 5%
)
```

### 3. Regular Backups

SQLite databases are single files - back them up regularly:

```bash
# Simple backup
cp sportsdata.db sportsdata.db.backup

# Backup with date
cp sportsdata.db "backup_$(date +%Y%m%d).db"

# Export to CSV for portability
python3 tools/data_import_export.py export-games --output games_backup.csv
python3 tools/data_import_export.py export-bets --output bets_backup.csv
```

### 4. Use Transactions for Bulk Operations

For importing large datasets, use transactions:

```python
# The manager handles transactions automatically
# But for custom operations:
cursor = manager.conn.cursor()
cursor.execute('BEGIN')
try:
    # Multiple inserts
    for game in games:
        manager.add_game(game)
    manager.conn.commit()
except Exception as e:
    manager.conn.rollback()
    raise
```

### 5. Close Connections

Always close the manager when done:

```python
# Manual close
manager = SportsDataManager()
try:
    # Your code
    pass
finally:
    manager.close()

# Or use context manager (coming soon)
```

### 6. Validate Data Before Import

Check data quality before importing:

```python
import csv

# Check for required fields
required_fields = ['date', 'home_team', 'away_team']

with open('games.csv', 'r') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames

    missing = [f for f in required_fields if f not in headers]
    if missing:
        print(f"Missing required fields: {missing}")
    else:
        # Import
        count = manager.import_games_from_csv('games.csv', 'nfl')
```

### 7. Monitor Database Size

SQLite databases can grow large. Monitor and optimize:

```python
import os

# Check database size
db_size = os.path.getsize('sportsdata.db') / (1024 * 1024)  # MB
print(f"Database size: {db_size:.2f} MB")

# Optimize (reduces file size)
manager.conn.execute('VACUUM')
```

### 8. Use Indexes for Performance

The manager creates indexes automatically, but for custom queries:

```python
cursor = manager.conn.cursor()

# Create custom index
cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_custom
    ON bets(sport, date, result)
''')
```

## Troubleshooting

### Database Locked Error

If you get "database is locked" errors:

```python
# Use check_same_thread=False (already done in manager)
# Or close other connections:
manager1.close()
manager2 = SportsDataManager("same_db.db")
```

### Import Errors

For CSV import issues:

```bash
# Check file encoding
file -i mydata.csv

# Convert if needed
iconv -f ISO-8859-1 -t UTF-8 mydata.csv > mydata_utf8.csv

# Check for missing values
python3 -c "
import csv
with open('mydata.csv') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        missing = [k for k, v in row.items() if not v]
        if missing:
            print(f'Row {i}: missing {missing}')
"
```

### Query Performance

For slow queries on large datasets:

```python
# Add LIMIT to queries
games = manager.list_games(sport="nfl", limit=1000)

# Use date filters
games = manager.list_games(
    start_date="2024-01-01",
    end_date="2024-01-31",
    limit=100
)

# Check query plan
cursor = manager.conn.cursor()
cursor.execute('EXPLAIN QUERY PLAN SELECT * FROM games WHERE sport = ?', ('nfl',))
print(cursor.fetchall())
```

## Advanced Usage

### Custom Queries

For complex queries not covered by the API:

```python
cursor = manager.conn.cursor()

# Custom query
cursor.execute('''
    SELECT sport, COUNT(*) as count,
           SUM(profit) as total_profit,
           AVG(clv) as avg_clv
    FROM bets
    WHERE result = 'win'
    GROUP BY sport
    ORDER BY total_profit DESC
''')

results = cursor.fetchall()
for row in results:
    print(dict(row))
```

### Data Migration

Migrate from old storage to new system:

```python
# Export from old system to CSV
# Then import to new system
from tools.data_import_export import DataImportExport

importer = DataImportExport("new_sportsdata.db")
importer.import_bets_csv("old_bets.csv")
importer.import_games_json("old_games.json")
```

## API Reference

See the source code for complete API documentation:
- `lib/sports_data_manager.py` - Main data manager
- `tools/data_import_export.py` - Import/export utilities

For examples, see:
- `tests/test_sports_data_manager.py` - Test suite with usage examples
