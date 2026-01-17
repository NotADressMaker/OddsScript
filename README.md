# SportsBetLang - A Programming Language for Sports Betting

SportsBetLang is a domain-specific programming language designed specifically for sports betting analysis, bankroll management, and betting strategy development. It provides built-in functions for common betting calculations and a simple, intuitive syntax for betting operations.

## Features

### Core Language
- **Betting-specific syntax**: Create bets, parlays, and manage bankrolls with dedicated language constructs
- **Built-in betting functions**: Kelly criterion, expected value, odds conversions, vig calculator, and more
- **Odds format support**: American, decimal, and fractional odds
- **Bankroll management**: Tools for position sizing and risk management
- **Full programming language**: Variables, functions, loops, conditionals, arrays, dictionaries
- **Interactive REPL**: Test calculations and strategies interactively

### 🤖 NEW: AI Chat Assistant
- **Natural Language Queries**: Ask questions in plain English - "Predict LeBron's points tonight"
- **Conversational Sports Insights**: Player predictions, comparisons, and betting analysis
- **Multi-Sport Support**: NBA, NFL, MLB, NHL analytics powered by Claude AI
- **REST API**: FastAPI backend with interactive documentation
- **Interactive CLI**: Chat interface for real-time sports analysis

🚀 **[Quick Start Guide](QUICKSTART_AI_CHAT.md)** | 📖 **[Full AI Documentation](docs/AI_CHAT_ASSISTANT.md)**

### 👥 NEW: Social Features
- **User-Generated Predictions**: Share predictions and track performance publicly
- **Community Leaderboards**: Compete globally or by sport on ROI, win rate, streak
- **Discussion Threads**: Forums for strategy, analysis, and betting insights
- **Follow Analysts**: Follow top performers and get their activity feeds
- **Engagement**: Like, comment, and interact with the community
- **Reputation System**: Build credibility with verified performance

🚀 **[Quick Start Guide](QUICKSTART_SOCIAL.md)** | 📖 **[Full Social Documentation](docs/SOCIAL_FEATURES.md)**

### 🔌 NEW: Developer API (Pro)
- **API Keys**: Generate keys for third-party integrations
- **Webhooks**: Real-time event notifications for your apps
- **Custom Data Feeds**: Export predictions, leaderboards, and analytics
- **Rate Limiting**: Tier-based limits (Free: 1k/day, Pro: 100k/day, Enterprise: Unlimited)
- **White-Label Solutions**: Custom-branded platforms (Enterprise)
- **Full REST API**: Complete programmatic access to all features

📖 **[Developer Documentation](docs/DEVELOPER_API.md)** | 🔧 **[API Examples](examples/developer_examples.py)**

### Packages and Tools
- **Standard Library**: Statistics, backtesting, CLV tracking, variance analysis, Poisson calculator, correlation analysis, regression modeling, multi-outcome Kelly
- **Betting Strategies**: Martingale, Fibonacci, Flat Betting implementations
- **CLI Tools**: 20+ professional tools including odds calculator, bet tracker, portfolio optimizer, line tracker, tax calculator, arbitrage finder, hedge calculator, market maker, and more
- **Testing Framework**: Comprehensive unit tests for all components
- **10 Example Programs**: From basic bets to advanced arbitrage and hedging

📚 **[View Complete Package Documentation](PACKAGES.md)** - 20+ tools and libraries

**Advanced Professional Tools:**
- 🎯 **Portfolio Optimizer** - Optimize bet allocation using Modern Portfolio Theory
- 📈 **Line Tracker** - Detect steam moves and sharp action
- ⚽ **Poisson Calculator** - Goal/point probabilities for totals betting
- 💰 **Tax Calculator** - US gambling tax calculator with 2024 brackets
- 🔍 **Correlation Analysis** - Avoid correlated parlay mistakes
- 📊 **Performance Attribution** - Identify your edge by sport, bet type, etc.
- ⚡ **Arbitrage Calculator** - Find guaranteed profit across multiple books
- 🛡️ **Hedge Calculator** - Optimal hedging for parlays, futures, middles
- 🏢 **Market Maker** - Calculate fair odds, remove vig, find value
- 📉 **Regression Analysis** - Build custom betting models
- 🎲 **Multi-Outcome Kelly** - Kelly criterion for 3+ outcomes (horse racing, golf, etc.)

## Installation

SportsBetLang requires Python 3.7 or higher.

```bash
# Clone the repository
git clone <repository-url>
cd programminglangauage

# Make the main script executable
chmod +x sportsbetlang.py

# Run the REPL
./sportsbetlang.py

# Or run a script
./sportsbetlang.py examples/01_basic_bet.odds
```

## Quick Start

### Basic Syntax

```sportsbetlang
# Variables
let bankroll = 1000
const unit_size = 10

# Print output
print("Bankroll: $" + bankroll)

# Arithmetic
let profit = 100 * 1.5
let total = bankroll + profit
```

### Creating Bets

```sportsbetlang
# Moneyline bet
bet "Lakers" odds -110 stake 100

# Spread bet
bet spread "Chiefs" odds -110 stake 50

# Parlay
parlay [bet1, bet2, bet3] stake 100
```

### Odds Calculations

```sportsbetlang
# Convert American odds to decimal
let decimal_odds = american_to_decimal(-110)  # Returns 1.909

# Calculate implied probability
let prob = implied_probability(-110)  # Returns 0.524 (52.4%)

# Calculate expected value
let ev = calculate_ev(0.55, -110, 100)  # true_prob, odds, stake

# Kelly criterion for bet sizing
let kelly = kelly_criterion(0.55, -110)
```

### Control Flow

```sportsbetlang
# Conditionals
if ev > 0 {
    print("Positive EV - place the bet!")
} else {
    print("Negative EV - skip it")
}

# Loops
for game in games {
    print(game)
}

while bankroll > 0 {
    # Betting logic
}
```

### Functions

```sportsbetlang
func analyze_bet(true_prob, odds, stake) {
    let ev = calculate_ev(true_prob, odds, stake)
    let kelly = kelly_criterion(true_prob, odds)

    if ev > 0 {
        print("Value bet! Kelly: " + kelly)
        return kelly
    }
    return 0
}

let bet_size = analyze_bet(0.60, -110, 100)
```

## Built-in Functions

### Odds Conversion

- `american_to_decimal(odds)` - Convert American odds to decimal format
- `decimal_to_american(odds)` - Convert decimal odds to American format
- `implied_probability(odds)` - Calculate implied probability from American odds

### Betting Analysis

- `calculate_ev(true_prob, odds, stake)` - Calculate expected value of a bet
- `kelly_criterion(true_prob, odds)` - Optimal bet sizing using Kelly criterion
- `break_even_percentage(odds)` - Required win rate to break even

### Parlay Functions

- `parlay_odds(odds1, odds2, ...)` - Calculate combined parlay odds
- `parlay_probability(prob1, prob2, ...)` - Probability of hitting all legs
- `round_robin(bets_count, parlay_size)` - Calculate round robin combinations

### Market Analysis

- `vig_calculator(odds1, odds2)` - Calculate bookmaker's vig from a two-way market
- `true_odds_from_vig(odds, total_vig)` - Remove vig to find true odds
- `units_to_risk(odds, units_to_win)` - Calculate units needed to risk

### Utility Functions

- `roi_calculator(wins, losses, avg_odds)` - Calculate ROI from betting record
- Standard math: `abs()`, `min()`, `max()`, `sqrt()`, `pow()`
- Array functions: `len()`, `sum()`, `range()`

## Examples

The `examples/` directory contains comprehensive examples:

### Basic Examples
1. **01_basic_bet.odds** - Basic betting operations and calculations
2. **02_kelly_criterion.odds** - Optimal bet sizing using Kelly criterion
3. **03_parlay.odds** - Parlay betting and analysis
4. **04_vig_calculator.odds** - Understanding bookmaker's vig
5. **05_bankroll_management.odds** - Bankroll management simulation
6. **06_odds_conversion.odds** - Converting between odds formats
7. **07_advanced_strategy.odds** - Advanced betting strategy with EV analysis

### Advanced Examples
8. **08_arbitrage_betting.odds** - Arbitrage opportunity detection
9. **09_monte_carlo_simulation.odds** - Monte Carlo bankroll simulation
10. **10_hedging_calculator.odds** - Hedging strategies and middle opportunities

### Running Examples

```bash
# Run an example
./sportsbetlang.py examples/02_kelly_criterion.odds

# Or using Python directly
python3 sportsbetlang.py examples/02_kelly_criterion.odds
```

## Language Reference

### Data Types

- **Numbers**: `42`, `3.14`, `-110`
- **Strings**: `"Lakers"`, `'Chiefs'`
- **Booleans**: `true`, `false`
- **Arrays**: `[1, 2, 3]`, `["Lakers", "Celtics"]`
- **Dictionaries**: `{"team": "Lakers", "odds": -110}`

### Operators

- **Arithmetic**: `+`, `-`, `*`, `/`, `%`
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical**: `and`, `or`, `not`
- **Assignment**: `=`

### Keywords

```
bet, bankroll, odds, stake, parlay
let, const, if, else, while, for, in
func, return, print
team, game, over, under, spread, moneyline, total
calculate, kelly, ev, implied, probability
true, false, and, or, not
```

## REPL Mode

Start the interactive REPL:

```bash
./sportsbetlang.py
```

```
SportsBetLang v1.0 - Sports Betting Programming Language
Type 'exit' or 'quit' to exit, 'help' for help

>>> let odds = -110
>>> implied_probability(odds)
0.5238095238095238
>>> calculate_ev(0.55, odds, 100)
2.7272727272727266
```

## Use Cases

### Bankroll Management

```sportsbetlang
let bankroll = 5000
let unit = bankroll * 0.01  # 1% units

func calculate_bet_size(edge, odds) {
    let kelly = kelly_criterion(edge, odds)
    return bankroll * kelly * 0.25  # Quarter Kelly
}
```

### Line Shopping

```sportsbetlang
let book1_odds = -110
let book2_odds = -105
let book3_odds = -108

let best_odds = max(book1_odds, book2_odds, book3_odds)
print("Best odds: " + best_odds)
```

### Expected Value Analysis

```sportsbetlang
func should_bet(team, my_probability, market_odds, min_edge) {
    let market_prob = implied_probability(market_odds)
    let edge = my_probability - market_prob

    if edge >= min_edge {
        let ev = calculate_ev(my_probability, market_odds, 100)
        print(team + " - Edge: " + (edge * 100) + "% | EV: $" + ev)
        return true
    }
    return false
}

should_bet("Lakers", 0.58, -110, 0.05)
```

### Parlay Analysis

```sportsbetlang
# Analyze a 3-leg parlay
let leg1 = -110
let leg2 = -120
let leg3 = +150

let parlay = parlay_odds(leg1, leg2, leg3)
let prob = parlay_probability(0.52, 0.55, 0.40)

print("Parlay odds: " + parlay)
print("Win probability: " + (prob * 100) + "%")
```

## Advanced Features

### Custom Betting Systems

```sportsbetlang
func martingale(base_bet, losses) {
    let multiplier = pow(2, losses)
    return base_bet * multiplier
}

func fibonacci_bet(base_bet, position) {
    if position <= 1 {
        return base_bet
    }
    return fibonacci_bet(base_bet, position - 1) + fibonacci_bet(base_bet, position - 2)
}
```

### Portfolio Management

```sportsbetlang
let bets = [
    {"team": "Lakers", "odds": -110, "stake": 100},
    {"team": "Chiefs", "odds": -120, "stake": 150},
    {"team": "Yankees", "odds": +120, "stake": 75}
]

let total_risk = 0
for bet in bets {
    total_risk = total_risk + bet["stake"]
}

print("Total risk: $" + total_risk)
```

## Best Practices

1. **Use Kelly Criterion wisely**: Consider fractional Kelly (1/4 or 1/2) for reduced variance
2. **Always calculate EV**: Never bet without positive expected value
3. **Account for vig**: Remove bookmaker's margin to find true odds
4. **Manage bankroll**: Never risk more than 1-5% of bankroll on a single bet
5. **Track everything**: Log all bets for performance analysis
6. **Shop for lines**: Always get the best available odds
7. **Avoid parlays**: They're typically -EV unless you have significant edge on each leg

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

MIT License - feel free to use and modify as needed.

## Disclaimer

This software is for educational and analytical purposes only. Sports betting involves risk. Always bet responsibly and within your means. Check your local laws regarding sports betting.

## Packages and Utilities

### Standard Library
- **Statistics Module** (`lib/statistics.py`) - Mean, median, std dev, Sharpe ratio, max drawdown, and more
- **Backtesting Framework** (`lib/backtesting.py`) - Test strategies on historical data or Monte Carlo simulations
- **CLV Tracker** (`lib/clv_tracker.py`) - Track Closing Line Value, the #1 indicator of long-term success
- **Variance Calculator** (`lib/variance_calc.py`) - Calculate variance, risk of ruin, required bankroll
- **Poisson Calculator** (`lib/poisson_calculator.py`) - Goal/point probabilities for totals betting
- **Correlation Analysis** (`lib/correlation_analysis.py`) - Detect correlated parlay legs
- **Regression Analysis** (`lib/regression_analysis.py`) - Build betting models with linear/multiple regression
- **Multi-Outcome Kelly** (`lib/multi_outcome_kelly.py`) - Kelly criterion for 3+ outcomes

### Betting Strategies
- **Martingale** (`strategies/martingale.py`) - Classic doubling strategy (high risk)
- **Fibonacci** (`strategies/fibonacci.py`) - Fibonacci sequence progression
- **Flat Betting** (`strategies/flat_betting.py`) - Recommended safe strategy

### Command-Line Tools

**Performance & Tracking:**
- **Bet Tracker** (`tools/bet_tracker.py`) - Track and analyze your betting performance
- **Performance Attribution** (`tools/performance_attribution.py`) - Identify edge sources by sport, bet type, book, etc.

**Calculations & Analysis:**
- **Odds Calculator** (`tools/odds_calc.py`) - Quick calculations for Kelly, EV, parlays, vig
- **Teaser Calculator** (`tools/teaser_calc.py`) - NFL/NBA teasers with Wong teaser detection
- **Round Robin Calculator** (`tools/round_robin_calc.py`) - All parlay combinations and scenarios
- **Bonus Calculator** (`tools/bonus_calc.py`) - Optimize sportsbook bonuses and promos
- **Tax Calculator** (`tools/tax_calculator.py`) - US gambling tax calculation (2024 brackets)
- **Arbitrage Calculator** (`tools/arbitrage_calculator.py`) - Find guaranteed profit opportunities across books
- **Hedge Calculator** (`tools/hedge_calculator.py`) - Optimal hedging for parlays, futures, and middles
- **Market Maker** (`tools/market_maker.py`) - Calculate fair odds, remove vig, find value bets

**Advanced Analysis:**
- **Portfolio Optimizer** (`tools/portfolio_optimizer.py`) - Optimize bet allocation using Modern Portfolio Theory
- **Line Tracker** (`tools/line_tracker.py`) - Track line movements and detect steam/sharp action
- **Bankroll Simulator** (`tools/bankroll_sim.py`) - Simulate strategies with ASCII visualization

### Testing
- **Test Suite** (`tests/test_interpreter.py`) - Comprehensive unit tests

📚 **[Complete package documentation and usage examples](PACKAGES.md)**

## Quick Tool Examples

```bash
# Calculate Kelly criterion
python3 tools/odds_calc.py kelly --prob 0.55 --odds -110 --bankroll 1000

# Track a bet
python3 tools/bet_tracker.py add NFL "Chiefs vs Bills" "Chiefs -3" \
    --odds -110 --stake 100

# View your betting stats
python3 tools/bet_tracker.py stats

# Run tests
python3 tests/test_interpreter.py
```

## Future Enhancements

Potential features for future versions:

- [ ] Real-time odds API integration
- [x] ~~Historical data analysis~~ ✓ (Backtesting framework, Performance attribution)
- [ ] Graphical visualizations (ASCII visualization available)
- [x] ~~Betting strategy backtesting~~ ✓ (lib/backtesting.py)
- [x] ~~Multi-sport support with sport-specific functions~~ ✓ (Poisson for soccer/hockey, teaser calc for NFL/NBA)
- [ ] Live betting calculations
- [ ] Web interface
- [x] ~~Line movement tracking~~ ✓ (tools/line_tracker.py)
- [x] ~~Tax calculation~~ ✓ (tools/tax_calculator.py)
- [x] ~~Portfolio optimization~~ ✓ (tools/portfolio_optimizer.py)

## Contact

For questions, issues, or suggestions, please open an issue on GitHub.

---

**Happy betting, and remember: Only bet what you can afford to lose!**
