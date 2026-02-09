# SportsBetLang Language Reference

## Overview
SportsBetLang is a lightweight DSL for expressing sports betting logic, calculations, and basic control flow. Programs are executed by the interpreter or compiled via code generation.

## Syntax Overview
- Statements are newline-separated.
- Blocks use braces `{ ... }`.
- Variables are introduced with `let` (mutable) or `const` (immutable).
- Functions are defined with `func` and return using `return`.

## Grammar Summary (Informal)
```
program       := statement* EOF
statement     := let_decl | const_decl | assignment | if_stmt | while_loop | for_loop
              | func_def | return_stmt | bet_stmt | parlay_stmt | expr_stmt

let_decl      := 'let' IDENT '=' expression
const_decl    := 'const' IDENT '=' expression
assignment    := IDENT '=' expression
if_stmt       := 'if' expression '{' statement* '}' ('else' '{' statement* '}')?
while_loop    := 'while' expression '{' statement* '}'
for_loop      := 'for' IDENT 'in' expression '{' statement* '}'
func_def      := 'func' IDENT '(' params? ')' '{' statement* '}'
return_stmt   := 'return' expression?

expression    := logical_or
logical_or    := logical_and ('or' logical_and)*
logical_and   := equality ('and' equality)*
equality      := comparison (('==' | '!=') comparison)*
comparison    := additive (('<' | '>' | '<=' | '>=') additive)*
additive      := multiplicative (('+' | '-') multiplicative)*
multiplicative:= unary (('*' | '/' | '%') unary)*
unary         := ('-' | 'not') unary | postfix
postfix       := primary (call | index | member)*
primary       := NUMBER | STRING | TRUE | FALSE | IDENT | '(' expression ')' | array | dict
array         := '[' (expression (',' expression)*)? ']'
dict          := '{' (expression ':' expression (',' expression ':' expression)*)? '}'
```

## Built-in Functions
Core utilities are available by default:
- `american_to_decimal(odds)`
- `decimal_to_american(odds)`
- `implied_probability(odds)`
- `calculate_ev(true_prob, odds, stake)`
- `kelly_criterion(true_prob, odds)`
- `parlay_odds(odds1, odds2, ...)`
- `parlay_probability(prob1, prob2, ...)`
- `break_even_percentage(odds)`
- `vig_calculator(odds1, odds2)`
- `true_odds_from_vig(odds, total_vig)`
- `units_to_risk(odds, units_to_win)`
- `roi_calculator(wins, losses, avg_odds)`
- `round_robin(bets_count, parlay_size)`
- `to_json(value)`
- `to_csv(rows)`
- Standard math: `abs`, `min`, `max`, `sqrt`, `pow`, `len`, `range`, `sum`

## Operators
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Boolean: `and`, `or`, `not`

## Examples

### Moneyline / Spread / Totals
```
let bankroll = 1000
bet moneyline "Lakers" odds -110 stake 50
bet spread "Chiefs" odds -105 stake 40 spread -3.5
bet total "Celtics vs Knicks" odds -110 stake 30
```

### EV + Kelly Sizing
```
let true_prob = 0.56
let odds = -110
let ev = calculate_ev(true_prob, odds, 100)
let kelly = kelly_criterion(true_prob, odds)
print("EV: " + to_json(ev))
print("Kelly fraction: " + to_json(kelly))
```

### Filters / Projections
```
let games = [
  {"team": "A", "line": 210, "projected": 215},
  {"team": "B", "line": 205, "projected": 200},
]

for game in games {
  if game.projected > game.line {
    print(game.team)
  }
}
```
