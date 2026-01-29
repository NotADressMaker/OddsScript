# SportsBetLang Language Specification

This document formalizes SportsBetLang syntax and semantics so the language can evolve consistently alongside the parser and interpreter.

## 1) Lexical Structure

### 1.1 Tokens

**Literals**
- `NUMBER`: integer or decimal literal (e.g., `42`, `3.14`)
- `STRING`: quoted string with escapes (e.g., `"hello"`, `'hi'`)
- `true`, `false`: boolean literals

**Identifiers**
- `IDENTIFIER`: letter/underscore followed by letters, digits, or underscores

**Keywords**
- `let`, `const`, `func`, `return`, `if`, `else`, `while`, `for`, `in`, `print`
- `bet`, `parlay`, `odds`, `stake`, `spread`, `moneyline`, `total`
- `import`, `from`, `as`
- Logical operators: `and`, `or`, `not`

**Operators**
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Assignment: `=`

**Delimiters**
- `(`, `)`, `{`, `}`, `[`, `]`, `,`, `.`, `:`

### 1.2 Comments and Whitespace
- Line comments begin with `#` and continue to the end of the line.
- Newlines separate statements; extra whitespace is ignored.

## 2) Grammar (EBNF)

Notation: `{ X }` means “zero or more”; `[ X ]` means “optional”.

```
program            = { statement } ;

statement          = variable_declaration
                   | assignment
                   | if_statement
                   | while_loop
                   | for_loop
                   | function_def
                   | return_statement
                   | bet_statement
                   | parlay_statement
                   | import_statement
                   | from_import_statement
                   | print_statement
                   | expression_statement ;

variable_declaration = ("let" | "const") identifier "=" expression ;
assignment           = identifier "=" expression ;
return_statement     = "return" [ expression ] ;
print_statement      = "print" "(" [ expression { "," expression } ] ")" ;
expression_statement = expression ;

if_statement       = "if" expression block [ "else" block ] ;
while_loop         = "while" expression block ;
for_loop           = "for" identifier "in" expression block ;
function_def       = "func" identifier "(" [ identifier { "," identifier } ] ")" block ;
block              = "{" { statement } "}" ;

import_statement    = "import" module_path [ "as" identifier ] ;
from_import_statement = "from" module_path "import" import_list ;
import_list         = import_item { "," import_item } ;
import_item         = identifier [ "as" identifier ] ;
module_path         = string | identifier { "." identifier } ;

bet_statement      = "bet" [ bet_type ] expression
                     [ "odds" expression ]
                     [ "stake" expression ]
                     { bet_param } ;
bet_type           = "spread" | "moneyline" | "total" ;
bet_param          = "spread" expression ;

parlay_statement   = "parlay" expression [ "stake" expression ] ;

expression         = or_expression ;
or_expression      = and_expression { "or" and_expression } ;
and_expression     = equality_expression { "and" equality_expression } ;
equality_expression = comparison_expression { ("==" | "!=") comparison_expression } ;
comparison_expression = additive_expression { ("<" | "<=" | ">" | ">=") additive_expression } ;
additive_expression    = multiplicative_expression { ("+" | "-") multiplicative_expression } ;
multiplicative_expression = unary_expression { ("*" | "/" | "%") unary_expression } ;
unary_expression   = [ "-" | "not" ] postfix_expression ;
postfix_expression = primary_expression { call | index | member } ;
call               = "(" [ expression { "," expression } ] ")" ;
index              = "[" expression "]" ;
member             = "." identifier ;

primary_expression = number
                   | string
                   | "true"
                   | "false"
                   | identifier
                   | "(" expression ")"
                   | array_literal
                   | dict_literal ;

array_literal      = "[" [ expression { "," expression } ] "]" ;
dict_literal       = "{" [ dict_pair { "," dict_pair } ] "}" ;
dict_pair          = expression ":" expression ;

identifier         = IDENTIFIER ;
number             = NUMBER ;
string             = STRING ;
```

## 3) Semantics

### 3.1 Values and Types
- Values are dynamically typed: numbers, strings, booleans, arrays, dictionaries, bets, and modules.
- Arrays support indexing with `[]`. Dictionaries use string or value keys and allow `dict.key` access.

### 3.2 Variables and Scope
- `let` defines mutable variables; `const` defines immutable variables.
- Each function call introduces a new lexical scope.
- Loops create a nested scope for loop variables.

### 3.3 Control Flow
- `if` evaluates its condition; non-zero, non-empty, non-null values are truthy.
- `while` loops while the condition is truthy.
- `for x in iterable` iterates arrays and other iterable values (from built-ins).

### 3.4 Functions
- Functions are first-class values declared with `func`.
- Calling a function evaluates arguments left-to-right and binds them by position.
- `return` exits the current function with an optional value.

### 3.5 Imports and Modules
- `import module` binds a module namespace to the last segment of the module path.
  - Example: `import betting` binds `betting`.
- `import module as alias` binds the module namespace to `alias`.
  - Example: `import stats as s` binds `s`.
- `from module import name [as alias]` binds one or more module exports directly into scope.

### 3.6 Betting Statements
- `bet` creates a bet object and returns it.
- `parlay` creates a parlay object composed of bet expressions.
- Additional betting parameters (like `spread`) are passed to the bet object.

### 3.7 Errors
- Accessing an undefined variable or member raises a runtime error.
- Reassigning a `const` raises a runtime error.
- Importing an unknown module raises a runtime error.
