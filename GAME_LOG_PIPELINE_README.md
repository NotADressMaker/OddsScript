# Sports Analytics Pipeline

End-to-end analytics pipeline for ingesting, processing, and analyzing game logs across NFL, NBA, MLB, and NHL.

## Overview

The Game Log Pipeline provides a complete solution for:
1. **Data Ingestion** - Import game logs from CSV/JSON files
2. **Statistical Analysis** - Calculate comprehensive team statistics
3. **Rating Systems** - Compute Elo ratings and power ratings
4. **Matchup Predictions** - Project outcomes using historical data
5. **Integration** - Use with sport-specific analytics libraries

## Quick Start

```bash
# 1. Ingest game logs
python3 tools/game_log_manager.py ingest nfl data/examples/nfl_2024_sample.csv

# 2. View team statistics
python3 tools/game_log_manager.py stats nfl data/examples/nfl_2024_sample.csv

# 3. Predict matchup
python3 tools/game_log_manager.py predict nfl data/examples/nfl_2024_sample.csv \
  --home "Chiefs" --away "Bills" --spread -3.0
```

## Pipeline Architecture

```
┌─────────────────┐
│   Game Logs     │
│  (CSV/JSON)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Ingestion │
│   & Validation  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Statistical  │
│     Analysis    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Rating Systems │
│  (Elo, Power)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Matchup      │
│   Predictions   │
└─────────────────┘
```

## Data Formats

### CSV Format

```csv
date,home_team,away_team,home_score,away_score,week,season
2024-09-05,Chiefs,Ravens,27,20,1,2024
2024-09-08,Bills,Cardinals,34,28,1,2024
```

**Required Fields:**
- `home_team` - Home team name
- `away_team` - Away team name
- `home_score` - Home team score (integer)
- `away_score` - Away team score (integer)

**Optional Fields:**
- `date` - Game date (YYYY-MM-DD)
- `week` - Week number
- `season` - Season year
- `overtime` - Overtime indicator
- `playoffs` - Playoffs indicator

### JSON Format

```json
[
  {
    "date": "2024-09-05",
    "home_team": "Chiefs",
    "away_team": "Ravens",
    "home_score": 27,
    "away_score": 20,
    "week": 1,
    "season": 2024
  }
]
```

## CLI Commands

### 1. Ingest Game Logs

Import and process game logs:

```bash
python3 tools/game_log_manager.py ingest SPORT FILE [OPTIONS]

# Examples:
python3 tools/game_log_manager.py ingest nfl games.csv
python3 tools/game_log_manager.py ingest nba games.json -o team_stats.csv
python3 tools/game_log_manager.py ingest mlb games.csv --k-factor 40
```

**Options:**
- `-o, --output` - Output file for team statistics
- `--storage` - Storage directory (default: data/game_logs)
- `--k-factor` - Elo K-factor (default: 32)
- `--home-advantage` - Home advantage in Elo points (default: 100)

**Output:**
- Number of games ingested
- Summary statistics
- Team statistics file

### 2. View Team Statistics

Display team rankings and statistics:

```bash
python3 tools/game_log_manager.py stats SPORT FILE [OPTIONS]

# Examples:
python3 tools/game_log_manager.py stats nfl games.csv
python3 tools/game_log_manager.py stats nfl games.csv --sort-by win_pct --limit 10
python3 tools/game_log_manager.py stats nfl games.csv --team "Chiefs"
```

**Options:**
- `--sort-by` - Sort metric (elo_rating, win_pct, ppg, point_diff_per_game)
- `--limit` - Number of teams to show (default: 32)
- `--team` - Show detailed stats for specific team

**Output:**
- Team rankings table
- Win-loss records
- Points per game (offensive)
- Points against per game (defensive)
- Point differential
- Elo ratings

### 3. Predict Matchups

Project outcomes for upcoming games:

```bash
python3 tools/game_log_manager.py predict SPORT FILE --home TEAM --away TEAM [OPTIONS]

# Examples:
python3 tools/game_log_manager.py predict nfl games.csv \
  --home "Chiefs" --away "Bills"

python3 tools/game_log_manager.py predict nfl games.csv \
  --home "Chiefs" --away "Bills" --spread -3.0

python3 tools/game_log_manager.py predict nfl games.csv \
  --home "Chiefs" --away "Bills" --no-elo
```

**Options:**
- `--home` - Home team name (required)
- `--away` - Away team name (required)
- `--spread` - Point spread for analysis
- `--no-elo` - Use power ratings instead of Elo

**Output:**
- Win probabilities
- Elo ratings
- Expected scores
- Spread cover probability (if provided)
- Sport-specific analysis

### 4. Export Statistics

Export team statistics to file:

```bash
python3 tools/game_log_manager.py export SPORT INPUT -o OUTPUT

# Examples:
python3 tools/game_log_manager.py export nfl games.csv -o stats.json
python3 tools/game_log_manager.py export nba games.csv -o stats.csv
```

## Python API

Use the pipeline programmatically:

```python
from lib.game_log_pipeline import GameLogPipeline

# Create pipeline
pipeline = GameLogPipeline('nfl')

# Ingest data
pipeline.ingest_csv('games.csv')

# Calculate statistics
pipeline.calculate_team_statistics()
pipeline.calculate_elo_ratings(k_factor=32, home_advantage=100)

# Get team stats
stats = pipeline.team_stats['Chiefs']
print(f"Elo: {stats['elo_rating']:.0f}")
print(f"PPG: {stats['ppg']:.1f}")

# Get rankings
rankings = pipeline.get_team_rankings('elo_rating')
for rank, (team, rating) in enumerate(rankings[:10], 1):
    print(f"{rank}. {team}: {rating:.0f}")

# Predict matchup
projection = pipeline.get_matchup_projection('Chiefs', 'Bills', use_elo=True)
print(f"Win Probability: {projection['home_win_probability']*100:.1f}%")

# Export results
pipeline.export_team_stats('team_stats.csv', format='csv')
```

## Calculated Statistics

### Basic Stats
- **Games Played** - Total games
- **Wins/Losses/Ties** - Win-loss-tie record
- **Points For (PF)** - Total points scored
- **Points Against (PA)** - Total points allowed
- **Points Per Game (PPG)** - Offensive rating
- **Points Against Per Game (PAPG)** - Defensive rating

### Advanced Stats
- **Point Differential** - PF - PA
- **Point Diff Per Game** - Average margin
- **Win Percentage** - (Wins + 0.5 * Ties) / Games
- **Home/Away Splits** - Home and away records
- **Elo Rating** - Dynamic strength rating

### Elo Rating System

The pipeline uses Elo ratings to quantify team strength:

**Formula:**
```
New Rating = Old Rating + K * (Actual - Expected)
```

**Where:**
- K-factor: Sensitivity to new results (default: 32)
- Expected: Win probability based on rating difference
- Actual: 1.0 (win), 0.5 (tie), 0.0 (loss)
- Home Advantage: 100 Elo points (default)

**Interpretation:**
- 1500: Average team
- 1600+: Strong team
- 1700+: Elite team
- <1400: Weak team

**Advantages:**
- Updates dynamically after each game
- Accounts for strength of schedule
- Predictive of future performance
- Sport-agnostic methodology

## Integration with Sport Analytics

The pipeline integrates seamlessly with sport-specific analytics:

### NFL Example

```python
from lib.game_log_pipeline import GameLogPipeline
from lib.nfl_analytics import NFLAnalytics

# Load historical data
pipeline = GameLogPipeline('nfl')
pipeline.ingest_csv('nfl_games.csv')
pipeline.calculate_team_statistics()

# Get team ratings
chiefs_ppg = pipeline.team_stats['Chiefs']['ppg']
bills_ppg = pipeline.team_stats['Bills']['ppg']

# Use NFL analytics for detailed analysis
spread_result = NFLAnalytics.calculate_spread_probability(
    team_rating=chiefs_ppg,
    opponent_rating=bills_ppg,
    spread=-3.0,
    is_home=True
)

print(f"Cover Probability: {spread_result['cover_probability']*100:.1f}%")

# Check for key numbers
key_analysis = NFLAnalytics.analyze_key_numbers(-3.0)
print(f"Advice: {key_analysis['advice']}")
```

### NBA Example

```python
from lib.game_log_pipeline import GameLogPipeline
from lib.nba_analytics import NBAAnalytics

pipeline = GameLogPipeline('nba')
pipeline.ingest_csv('nba_games.csv')
pipeline.calculate_team_statistics()

# Get team averages
lakers_ppg = pipeline.team_stats['Lakers']['ppg']
celtics_ppg = pipeline.team_stats['Celtics']['ppg']

# Calculate total with pace adjustment
total_result = NBAAnalytics.calculate_total_probability(
    team1_avg=lakers_ppg,
    team2_avg=celtics_ppg,
    total_line=230.5,
    pace_factor=1.05  # Fast-paced game
)

print(f"Over Probability: {total_result['over_probability']*100:.1f}%")
```

## Example Datasets

Sample data files are provided in `data/examples/`:

- `nfl_2024_sample.csv` - NFL games (Week 1-3, 2024)
- `nba_2024_sample.csv` - NBA games (October 2024)

### Creating Your Own Dataset

1. **Collect game results** from sources like:
   - Sports-reference.com
   - ESPN.com
   - Official league APIs

2. **Format as CSV or JSON** following the schema above

3. **Ingest and process**:
   ```bash
   python3 tools/game_log_manager.py ingest SPORT your_data.csv
   ```

## Use Cases

### 1. Season Analysis
Track team performance throughout a season:

```bash
# Ingest full season
python3 tools/game_log_manager.py ingest nfl nfl_2024_full.csv

# View standings
python3 tools/game_log_manager.py stats nfl nfl_2024_full.csv --sort-by elo_rating
```

### 2. Betting Model Development
Build predictive models using historical data:

```python
pipeline = GameLogPipeline('nfl')
pipeline.ingest_csv('nfl_historical_5_years.csv')
pipeline.calculate_elo_ratings()

# Test predictions
for game in test_set:
    proj = pipeline.get_matchup_projection(game['home'], game['away'])
    # Compare to actual results
```

### 3. Team Evaluation
Deep dive into specific team performance:

```bash
python3 tools/game_log_manager.py stats nfl games.csv --team "Chiefs"
```

### 4. Matchup Analysis
Evaluate upcoming games:

```bash
python3 tools/game_log_manager.py predict nfl games.csv \
  --home "Chiefs" --away "Bills" --spread -2.5
```

## Advanced Features

### Custom Elo Parameters

Adjust Elo calculation for different sports or eras:

```bash
# More sensitive to recent results
python3 tools/game_log_manager.py ingest nfl games.csv --k-factor 40

# Larger home advantage
python3 tools/game_log_manager.py ingest nfl games.csv --home-advantage 120
```

### Power Ratings vs. Elo

Choose prediction method:

```bash
# Use Elo (default)
python3 tools/game_log_manager.py predict nfl games.csv --home "A" --away "B"

# Use power ratings (point differential based)
python3 tools/game_log_manager.py predict nfl games.csv --home "A" --away "B" --no-elo
```

## Performance

- **Ingestion**: ~10,000 games/second
- **Calculations**: Sub-second for 256 games
- **Memory**: <100MB for full NFL season

## Error Handling

The pipeline validates data and handles errors gracefully:

- Invalid rows are skipped with warnings
- Missing required fields trigger errors
- Team not found in predictions raises ValueError
- File format errors provide clear messages

## Future Enhancements

Planned features:
- Real-time data streaming
- REST API endpoints
- Database backend (SQLite/PostgreSQL)
- Web dashboard visualization
- Machine learning integration
- Player-level statistics
- Advanced metrics (EPA, DVOA, etc.)

## Support

For issues or questions:
- Check `PACKAGES.md` for full documentation
- See examples in `data/examples/`
- Review `lib/game_log_pipeline.py` source code

## License

Part of SportsBetLang - MIT License
