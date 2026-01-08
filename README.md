# TrackScript - A Programming Language for Horse Racing Betting

TrackScript is a domain-specific programming language designed specifically for horse racing betting analysis, handicapping, and wagering strategy development. It provides built-in functions for track takeout calculations, exotic bet analysis, and handicapping tools with an intuitive syntax tailored for the track.

## Features

### Core Language
- **Horse racing-specific syntax**: Create win/place/show bets, exactas, trifectas, superfectas, and more
- **Built-in racing functions**: Calculate payouts, track takeout, exotic bet combinations, handicapping ratios
- **Odds format support**: Track odds (fractional), decimal, and traditional formats
- **Bankroll management**: Tools for position sizing and risk management at the track
- **Handicapping tools**: Speed ratings, class analysis, pace calculations
- **Full programming language**: Variables, functions, loops, conditionals, arrays, dictionaries
- **Interactive REPL**: Test calculations and strategies interactively

### Advanced Packages (NEW!)
- **Breeding & Pedigree Analysis**: Dosage Index, Chef-de-Race, nick crosses, female family strength
- **Pattern Recognition**: Trainer/jockey angles, track biases, market inefficiencies
- **Arbitrage & Value Finding**: Overlay detection, true odds calculation, exotic value scoring
- **Race Simulation & Probability**: Monte Carlo simulation, Bayesian updates, Elo ratings, variance analysis

## Installation

TrackScript requires Python 3.7 or higher.

```bash
# Clone the repository
git clone <repository-url>
cd programminglangauage

# Make the main script executable
chmod +x trackscript.py

# Run the REPL
./trackscript.py

# Or run a script
./trackscript.py examples/01_basic_wager.track
```

## Quick Start

### Basic Syntax

```trackscript
# Variables
let bankroll = 1000
const unit_size = 20

# Print output
print("Bankroll: $" + bankroll)

# Arithmetic
let profit = 100 * 2.5
let total = bankroll + profit
```

### Creating Wagers

```trackscript
# Win bet on horse #5
wager win horse 5 odds 7-2 stake 20

# Place bet
wager place horse 3 odds 3-5 stake 40

# Exacta box
wager exacta box [5, 7, 8] stake 12

# Trifecta wheel
wager trifecta key 5 with [2, 7, 8, 9] stake 24

# Daily double
wager daily_double races [3, 4] horses [[2, 5], [1, 7]] stake 8
```

### Track Calculations

```trackscript
# Convert track odds to decimal
let decimal_odds = track_to_decimal("7-2")  # Returns 4.5

# Calculate win payout
let payout = win_payout("5-1", 20)  # $20 bet at 5-1

# Calculate track takeout
let net_pool = calculate_takeout(1000, 0.17)  # 17% takeout

# Exotic bet probabilities
let exacta_combos = exacta_combinations(8)  # 8 horses = 56 combos
let trifecta_combos = trifecta_combinations(10)  # 10 horses = 720 combos
```

### Handicapping

```trackscript
# Speed rating calculation
let speed = speed_rating(110.2, "fast", 6)  # time, track condition, furlongs

# Class rating
let class_rating = calculate_class_rating(10000, 5000)  # current vs last class

# Pace analysis
let early_pace = pace_rating([22.1, 45.3], 6)  # quarter splits, furlongs
```

### Control Flow

```trackscript
# Conditionals
if odds_value > 0 {
    print("Overlay - positive value bet!")
} else {
    print("Underlay - skip this race")
}

# Loops
for race in race_card {
    print(race)
}

while bankroll > minimum_stake {
    # Betting logic
}
```

### Functions

```trackscript
func analyze_horse(morning_line, true_odds, stake) {
    let value = calculate_odds_value(true_odds, morning_line)
    let overlay = overlay_percentage(true_odds, morning_line)

    if value > 0 {
        print("Value bet! Overlay: " + overlay + "%")
        return stake
    }
    return 0
}

let bet_amount = analyze_horse("7-2", "2-1", 20)
```

## Built-in Functions

### Odds Conversion

- `track_to_decimal(odds)` - Convert track odds (e.g., "5-2") to decimal format
- `decimal_to_track(odds)` - Convert decimal odds to track format
- `track_to_american(odds)` - Convert track odds to American format
- `american_to_track(odds)` - Convert American odds to track format
- `fractional_to_decimal(odds)` - Convert fractional odds to decimal

### Payout Calculations

- `win_payout(odds, stake)` - Calculate win bet payout
- `place_payout(odds, stake)` - Calculate place bet payout
- `show_payout(odds, stake)` - Calculate show bet payout
- `exacta_payout(odds, stake)` - Calculate exacta payout
- `trifecta_payout(odds, stake)` - Calculate trifecta payout
- `superfecta_payout(odds, stake)` - Calculate superfecta payout

### Track Analysis

- `calculate_takeout(pool_size, takeout_rate)` - Calculate net pool after takeout
- `breakage_adjustment(payout)` - Apply standard track breakage rules
- `odds_from_pool(horse_pool, total_pool, takeout)` - Calculate odds from pool sizes

### Exotic Bet Combinations

- `exacta_combinations(horses)` - Calculate possible exacta combinations
- `trifecta_combinations(horses)` - Calculate possible trifecta combinations
- `superfecta_combinations(horses)` - Calculate possible superfecta combinations
- `box_cost(bet_type, horses, unit_stake)` - Calculate cost of boxing a bet
- `wheel_cost(bet_type, key_horses, other_horses, unit_stake)` - Calculate wheel cost
- `key_cost(bet_type, key_horse, with_horses, unit_stake)` - Calculate key bet cost

### Handicapping Functions

- `speed_rating(time, track_condition, distance)` - Calculate speed figure
- `class_rating(current_class, previous_class)` - Analyze class change
- `pace_rating(splits, distance)` - Calculate pace figures
- `recency_factor(days_since_last)` - Calculate recency adjustment
- `jockey_trainer_combo(jockey_win_pct, trainer_win_pct)` - Combined statistics
- `track_bias_adjustment(post_position, bias_factor)` - Post position adjustment

### Wagering Strategy

- `kelly_racing(true_odds, track_odds, bankroll)` - Kelly criterion for racing
- `dutching(horses, odds, bankroll)` - Calculate dutching stakes
- `calculate_roi(wins, total_bets, avg_odds, avg_stake)` - Calculate ROI
- `overlay_percentage(true_odds, morning_line)` - Calculate overlay/underlay
- `calculate_odds_value(estimated_odds, actual_odds)` - Value calculation

### Utility Functions

- Standard math: `abs()`, `min()`, `max()`, `sqrt()`, `pow()`, `round()`
- Array functions: `len()`, `sum()`, `range()`, `sort()`

## Examples

The `examples/` directory contains comprehensive examples:

**Core Features:**
1. **01_basic_wager.track** - Basic win/place/show betting
2. **02_exotic_bets.track** - Exacta, trifecta, and superfecta examples
3. **03_handicapping.track** - Handicapping and speed ratings
4. **04_dutching.track** - Dutching multiple horses in a race
5. **05_bankroll_management.track** - Managing your track bankroll
6. **06_advanced_strategy.track** - Advanced betting strategies with value analysis

**Advanced Packages:**
7. **07_pedigree_analysis.track** - Dosage Index, breeding patterns, pedigree evaluation
8. **08_pattern_recognition.track** - Trainer/jockey angles, track biases, betting patterns
9. **09_arbitrage_value.track** - Arbitrage detection, value finding, market efficiency
10. **10_race_simulation.track** - Monte Carlo simulation, Bayesian updates, probability modeling

### Running Examples

```bash
# Run an example
./trackscript.py examples/02_exotic_bets.track

# Or using Python directly
python3 trackscript.py examples/03_handicapping.track
```

## Language Reference

### Data Types

- **Numbers**: `42`, `3.14`, `5.5`
- **Strings**: `"Secretariat"`, `'5-2'`, `"fast"`
- **Booleans**: `true`, `false`
- **Arrays**: `[1, 2, 3]`, `["Affirmed", "Seattle Slew"]`
- **Dictionaries**: `{"horse": 5, "odds": "7-2", "jockey": "Smith"}`

### Operators

- **Arithmetic**: `+`, `-`, `*`, `/`, `%`
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical**: `and`, `or`, `not`
- **Assignment**: `=`

### Keywords

```
wager, race, horse, jockey, trainer, track, post
win, place, show, exacta, trifecta, superfecta
daily_double, pick3, pick4, pick6
box, wheel, key, stake, odds
let, const, if, else, while, for, in
func, return, print
maiden, claiming, allowance, stakes
turf, dirt, synthetic, fast, muddy, sloppy
speed, class, pace, form
true, false, and, or, not
```

## REPL Mode

Start the interactive REPL:

```bash
./trackscript.py
```

```
TrackScript v1.0 - Horse Racing Programming Language
Type 'exit' or 'quit' to exit, 'help' for help

>>> let odds = track_to_decimal("5-2")
>>> print(odds)
3.5
>>> win_payout("5-2", 20)
70.0
```

## Use Cases

### Bankroll Management

```trackscript
let bankroll = 2000
let unit = bankroll * 0.02  # 2% units

func calculate_wager_size(overlay, odds) {
    let kelly = kelly_racing(overlay, odds, bankroll)
    return bankroll * kelly * 0.25  # Quarter Kelly
}
```

### Value Hunting

```trackscript
let morning_line = "7-2"
let my_line = "5-2"

let is_overlay = overlay_percentage(my_line, morning_line)

if is_overlay > 10 {
    print("Strong overlay - bet this horse!")
}
```

### Exotic Bet Strategy

```trackscript
# Calculate cost of boxing 4 horses in an exacta
let horses = [2, 5, 7, 9]
let box_bet_cost = box_cost("exacta", 4, 2)

print("Exacta box cost: $" + box_bet_cost)

# Wheel analysis
let key_horse = 5
let other_horses = [1, 3, 7, 8, 9]
let wheel_bet_cost = wheel_cost("exacta", 1, 5, 2)
print("Exacta wheel cost: $" + wheel_bet_cost)
```

### Dutching Example

```trackscript
# Dutch multiple horses in a race
let horses = [
    {"number": 3, "odds": "5-2"},
    {"number": 7, "odds": "4-1"},
    {"number": 8, "odds": "6-1"}
]

let total_stake = 100
let dutch_stakes = dutching(horses, total_stake)

for stake in dutch_stakes {
    print("Horse " + stake["horse"] + ": $" + stake["amount"])
}
```

### Handicapping System

```trackscript
func analyze_race(horses, race_conditions) {
    let top_picks = []

    for horse in horses {
        let speed_fig = speed_rating(horse["time"], race_conditions["surface"], 6)
        let class_fig = class_rating(horse["current_class"], horse["last_class"])
        let pace_fig = pace_rating(horse["splits"], 6)

        let total_rating = speed_fig + class_fig + pace_fig

        if total_rating > 85 {
            top_picks = top_picks + [horse]
        }
    }

    return top_picks
}
```

## Advanced Features

### Daily Double Strategy

```trackscript
func daily_double_strategy(race1_picks, race2_picks, bankroll) {
    let total_combos = len(race1_picks) * len(race2_picks)
    let cost_per_combo = 2
    let total_cost = total_combos * cost_per_combo

    if total_cost <= bankroll * 0.05 {
        print("DD wager approved: " + total_combos + " combos")
        return total_cost
    }

    print("Too expensive - reduce selections")
    return 0
}
```

### Pick-3 Wheel Calculator

```trackscript
let race1 = [2, 5]
let race2 = [1, 3, 7, 8]
let race3 = [4]

let total_combinations = len(race1) * len(race2) * len(race3)
let cost = total_combinations * 1  # $1 base bet

print("Pick-3 cost: $" + cost)
print("Combinations: " + total_combinations)
```

### Speed Figure Compilation

```trackscript
let speed_figs = []

for race in past_performances {
    let fig = speed_rating(race["time"], race["condition"], race["distance"])
    speed_figs = speed_figs + [fig]
}

let avg_speed = sum(speed_figs) / len(speed_figs)
let top_speed = max(speed_figs)

print("Average speed figure: " + avg_speed)
print("Top speed figure: " + top_speed)
```

## Advanced Packages

TrackScript includes four professional-grade packages for serious handicapping and wagering:

### Breeding & Pedigree Analysis Package

Analyze bloodlines and breeding patterns for distance/surface suitability.

**Functions:**
- `dosage_index(brilliant, intermediate, classic, solid, professional)` - Calculate Dosage Index (DI < 4.0 = router, DI > 4.0 = sprinter)
- `center_of_distribution(...)` - Calculate CD for speed/stamina balance
- `optimal_distance(dosage_index)` - Predict optimal racing distance
- `inbreeding_coefficient(duplications, generations)` - Calculate inbreeding level
- `surface_affinity(turf_wins, turf_starts, dirt_wins, dirt_starts)` - Determine surface preference
- `maiden_breaker_score(sire_wins, sire_starters)` - Predict maiden race success
- `distance_pedigree_rating(sire_dist, dam_dist, race_dist)` - Rate pedigree for specific distance
- `nick_multiplier(sire, broodmare_sire)` - Get multiplier for known successful crosses
- `female_family_strength(sw, graded, total_foals)` - Evaluate female family quality
- `workout_indicator(2yo_starts, 2yo_foals)` - Predict early maturity

**Example:**
```trackscript
let di = dosage_index(4, 3, 2, 1, 1)
let optimal = optimal_distance(di)
print("DI: " + di + " - Optimal: " + optimal)

if di < 3.0 {
    print("Suited for route races")
}
```

### Pattern Recognition Package

Identify profitable trainer/jockey angles and track biases.

**Trainer Patterns:**
- `layoff_pattern(trainer, days, wins, starts)` - Success after layoffs
- `first_time_starter_angle(wins, starts)` - FTS effectiveness rating
- `class_drop_specialist(drop_wins, drop_starts, raise_wins, raise_starts)` - Class drop expertise
- `distance_switch_pattern(...)` - Stretch out vs cut back success
- `surface_switch_specialist(turf_dirt_wins, starts)` - Surface switch skill
- `claiming_pattern(claims_won, claims_started, next_wins)` - First race after claim

**Jockey Patterns:**
- `running_style_affinity(early_wins, early_starts, late_wins, late_starts)` - Speed vs closer preference
- `track_specialist_rating(track_wins, track_starts, overall_wins, overall_starts)` - Track expertise
- `post_position_skill(rail_wins, outside_wins, ...)` - Post position skill
- `favorite_performance(fav_wins, fav_starts)` - Reliability on favorites

**Bias Detection:**
- `speed_bias_score(fr_wins, fr_starts, closer_wins, closer_starts)` - Detect speed/closing bias
- `rail_bias(rail_wins, middle_wins, outside_wins, ...)` - Post position bias
- `wet_track_specialists(wet_wins, fast_wins, ...)` - Off-track performance
- `pace_scenario_advantage(...)` - Contested vs uncontested pace preference

**Betting Patterns:**
- `overlay_finder(true_prob, ml_odds, current_odds)` - Identify overlays/underlays
- `chalk_eat_pattern(fav_won, fav_ran, avg_odds)` - Analyze favorite performance
- `late_money_indicator(opening_odds, current_odds)` - Detect smart money

**Example:**
```trackscript
let fts = first_time_starter_angle(95, 310)
print("FTS Rating: " + fts["rating"])
print("Profitable: " + fts["profitable"])

if fts["rating"] == "elite" {
    print("Strong angle - bet this debut")
}

let bias = speed_bias_score(35, 90, 12, 90)
if bias > 10 {
    print("Speed bias detected - favor front-runners")
}
```

### Arbitrage & Value Finding Package

Find guaranteed profits and exploit market inefficiencies.

**Arbitrage Detection:**
- `dutching_arbitrage(horses, takeout)` - Calculate if dutching guarantees profit
- `cross_track_arbitrage(track1_odds, track2_odds, ...)` - Find cross-track arbs
- `place_show_arbitrage(win_odds, place_odds, show_odds, runners)` - Detect place/show value

**Value Finding:**
- `true_odds_calculator(speed, class, pace, form, jockey, trainer)` - Calculate fair odds from factors
- `value_bet_calculator(estimated_odds, actual_odds, min_edge)` - Evaluate value bets
- `multi_race_parlay_value(races, min_roi)` - Analyze multi-race wager value
- `exotic_value_score(exotic_type, key_probs, exotic_odds)` - Evaluate exotic bet value

**Market Efficiency:**
- `favorite_longshot_bias(fav_roi, longshot_roi)` - Detect market bias
- `pool_size_inefficiency(pool, avg_pool, edge)` - Small pool opportunities
- `late_scratch_value(original_odds, scratched_favorite)` - Value from scratches

**Example:**
```trackscript
let true_odds = true_odds_calculator(92, 85, 88, 90, 75, 80)
let value = value_bet_calculator(true_odds, 4.5, 0.10)

print("Estimated odds: " + true_odds)
print("Actual odds: 4.5")
print("Edge: " + value["edge_pct"] + "%")

if value["is_value"] {
    print("VALUE BET - Kelly: " + (value["kelly_fraction"] * 100) + "%")
}

let ps_arb = place_show_arbitrage(3.5, 6.0, 8.5, 10)
if ps_arb["place_overlay"] {
    print("Overlay in place pool!")
}
```

### Race Simulation & Probability Package

Monte Carlo simulation and advanced probability modeling.

**Race Simulation:**
- `simulate_race(horses, num_simulations)` - Run Monte Carlo race simulation
- `simulate_exotic(exotic_type, horses, num_sims)` - Simulate exotic bet outcomes
- `variance_calculation(win_prob, odds, stake, num_bets)` - Calculate variance and bankroll needs

**Probability Modeling:**
- `bayesian_update(prior_prob, likelihood, evidence_strength)` - Update probability with new info
- `confidence_interval(estimated_prob, sample_size, confidence_level)` - Calculate confidence bounds
- `poisson_pace_model(early_pace, avg_pace, std_dev)` - Model pace scenarios
- `elo_rating_update(winner_rating, loser_rating, k_factor)` - Update Elo ratings
- `regression_to_mean(current, career_avg, races_back, max_weight)` - Adjust for regression

**Monte Carlo Strategies:**
- `optimal_bet_sizing(bankroll, win_prob, odds, simulations, target_kelly)` - Simulate optimal stake

**Example:**
```trackscript
# Update probability with new workout information
let prior = 0.35
let updated = bayesian_update(prior, 1.4, 0.8)
print("Updated probability: " + (updated * 100) + "%")

# Calculate variance
let var = variance_calculation(0.42, 2.8, 50, 100)
print("Expected profit: $" + var["total_expected_profit"])
print("Risk of ruin: " + var["risk_of_ruin_pct"] + "%")

# Regression to mean
let regressed = regression_to_mean(95, 85, 3, 0.7)
print("Regressed figure: " + regressed)

# Elo ratings
let ratings = elo_rating_update(1450, 1520, 32)
print("New rating: " + ratings[0])
```

### Package Usage Tips

1. **Breeding Package**: Use for 2YO races, turf debuts, route races
2. **Pattern Package**: Essential for trainer/jockey angles and track biases
3. **Arbitrage Package**: Daily tool for finding value and overlays
4. **Simulation Package**: Use for bankroll management and probability updates

**Combined Example:**
```trackscript
# Full analysis workflow
let di = dosage_index(4, 3, 2, 1, 1)
let fts = first_time_starter_angle(95, 310)
let true_odds = true_odds_calculator(90, 85, 88, 92, 78, 82)
let value = value_bet_calculator(true_odds, 4.2, 0.10)

if di < 3.5 and fts["profitable"] and value["is_value"] {
    let kelly = value["kelly_fraction"]
    print("STRONG BET: Multiple edges aligned")
    print("Kelly stake: " + (kelly * 100) + "% of bankroll")
}
```

## Best Practices

1. **Know the takeout**: Different bet types have different takeout rates - exotic bets usually have higher takeout
2. **Find overlays**: Only bet horses whose odds are higher than their true probability
3. **Manage bankroll**: Never risk more than 2-5% of bankroll on a single race
4. **Study the form**: Use speed figures, class ratings, and pace analysis
5. **Track your bets**: Log all wagers for performance analysis
6. **Understand exotic bet costs**: Box and wheel bets can get expensive quickly
7. **Value over favorites**: Betting every favorite is a losing strategy due to takeout
8. **Consider late scratches**: Always check for scratches before betting
9. **Post position matters**: Inside posts on turf, outside on dirt mile
10. **Weather and track conditions**: Adjust handicapping for off tracks

## Horse Racing Terminology

- **Win/Place/Show**: Straight bets on finishing positions
- **Exacta**: Pick first two horses in exact order
- **Trifecta**: Pick first three horses in exact order
- **Superfecta**: Pick first four horses in exact order
- **Box**: Bet covers all possible combinations
- **Wheel**: Key one horse with all others
- **Key**: Use a horse in specific position with others
- **Daily Double**: Pick winners of two consecutive races
- **Pick 3/4/5/6**: Pick winners of 3, 4, 5, or 6 consecutive races
- **Takeout**: Track's commission on betting pools
- **Overlay**: Horse with higher odds than true probability
- **Underlay**: Horse with lower odds than true probability
- **Morning Line**: Track handicapper's estimated odds

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

MIT License - feel free to use and modify as needed.

## Disclaimer

This software is for educational and analytical purposes only. Horse race betting involves risk. Always bet responsibly and within your means. Check your local laws regarding horse racing wagering. Must be 18+ to wager on horse racing.

## Future Enhancements

Potential features for future versions:

- [ ] Real-time track odds API integration
- [ ] Historical race data analysis
- [ ] Monte Carlo simulations for exotic bets
- [ ] Sharpe ratio calculations for handicapping systems
- [ ] Unit testing framework
- [ ] CSV/JSON race data import/export
- [ ] Visualization of pace charts and speed figures
- [ ] Betting strategy backtesting against historical data
- [ ] Track-specific bias analysis
- [ ] Trainer/jockey statistics integration
- [ ] Past performance parsing
- [ ] Live odds tracking and notification

## Contact

For questions, issues, or suggestions, please open an issue on GitHub.

---

**Good luck at the track, and remember: Only bet what you can afford to lose!**
