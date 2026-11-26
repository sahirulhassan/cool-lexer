# COOL Lexer — Complete Study & Viva Guide

> **Who this guide is for:** You and your teammates. If you have zero clue what a "lexical analyzer", "regex", or "maximal munch" is, start from Part 1 and read straight through. By the end, you will understand every line of code in this repo and be ready to pass the individual viva.

---

## Part 1: Prerequisite Topics (Zero-Jargon Crash Course)

### 1. Where does a Lexer fit in a compiler?

When you write code in a text file, the computer doesn't see "variables" or "if-statements"—it just sees one long string of characters like `f`, `a`, `c`, `t`, ` `, `:`, `:`, `=`, ...

A compiler processes that text in stages:

```text
Source Code (.cool file)
   │
   ▼
[ 1. Lexical Analyzer (Lexer / Scanner) ]   <-- THIS IS OUR PROJECT!
   │  Turns raw characters into labeled "Tokens"
   │  Throws away spaces, tabs, and // comments
   ▼
Token Stream (e.g., IDENTIFIER "fact", ASSIGN "::=", FUNC "func", ...)
   │
   ▼
[ 2. Parser ]  (Future assignment)
      Checks grammar rules using the tokens
```

**In one sentence:** The lexer's job is to read raw text from left to right, group characters into meaningful words/symbols (**tokens**), ignore whitespace and comments, track line numbers, and stop immediately if it sees an illegal character.

---

### 2. Core Vocabulary (Memorize These 6 Terms)

| Term | Plain-English Meaning | Example from `example.cool` |
| :--- | :--- | :--- |
| **Lexeme** | The exact raw characters matched in the source file. | `"fact"`, `"::="`, `"1"`, `"("` |
| **Token (Token Type)** | The category/label we assign to a lexeme. | `IDENTIFIER`, `ASSIGN`, `INT_LITERAL`, `LPAREN` |
| **Pattern** | The rule (written as a regular expression) that describes what lexemes belong to a token. | `[A-Za-z]+` matches words; `-?[0-9]+` matches integers |
| **Regular Expression (Regex)** | A compact mini-language for describing text patterns. | `//[^\r\n]*` means "`//` followed by anything until end of line" |
| **Maximal Munch (Longest Match)** | Always match the **longest** valid token starting at the current position—don't stop early. | `iffy` is one `IDENTIFIER "iffy"`, NOT `IF "if"` + `IDENTIFIER "fy"`. `>=` is one `IDENTIFIER ">="`, NOT `>` + `=`. |
| **Line Tracking** | Counting `\n` / `\r\n` / `\r` characters so every token and error knows which line it came from. | `LBRACE "{" [line 2]` |

---

### 3. Regex Cheat Sheet (Only What Our Code Actually Uses)

You don't need to know all of regex—just these building blocks used in `src/cool_lexer/lexer.py`:

| Regex Piece | Meaning | Example Match |
| :--- | :--- | :--- |
| `[ \t]+` | Space or tab, **1 or more times** (`+` = 1 or more) | `"   "` or `"\t "` |
| `[A-Za-z]+` | Any uppercase or lowercase letter, 1 or more times | `"fact"`, `"func"`, `"n"` |
| `[0-9]+` | Any digit `0`–`9`, 1 or more times | `"1"`, `"42"` |
| `-?` | An optional minus sign (`?` = 0 or 1 times) | Matches `"-7"` and `"7"` |
| `[^"\r\n]*` | Anything **except** (`^`) a quote `"`, `\r`, or `\n`, **0 or more times** (`*` = 0 or more) | `"hello, world"` (inside quotes) |
| `//[^\r\n]*` | `//` followed by any characters except newline | `"// this is a comment"` |
| `\|` | **OR** (try the left pattern first; if it doesn't match, try the right) | `==\|!=` matches `==` or `!=` |
| `\(` `\)` `\{` `\}` | Backslash escapes special regex characters so they match literally | Matches `(`, `)`, `{`, `}` |
| `.` | **Any** single character (except newline) | Used at the very end as `MISMATCH` to catch illegal characters like `@` |
| `(?P<NAME>...)` | A **named group** in Python `re` so we know *which* rule matched | `(?P<ASSIGN>::=)` lets `match.lastgroup` return `"ASSIGN"` |

---

### 4. Tools & Libraries Used in This Project (1-Sentence Each)

If the examiner asks *"What is `pydantic` / `uv` / `ruff` / `ty` doing here?"*:

- **`uv`**: A fast Python package and project manager that creates the `.venv` virtual environment and runs commands cleanly (`uv run ...`).
- **`pydantic`**: Validates our `Token` objects (e.g., guaranteeing `line >= 1`) and makes them immutable (`frozen=True`) so tokens can't be accidentally modified after creation.
- **`StrEnum`**: A Python enum whose values are strings, so `TokenType.FUNC.value` is `"FUNC"`.
- **`pytest`**: Runs our 28 automated tests to prove the lexer handles all valid tokens, edge cases, and error cases.
- **`ruff`**: Checks code formatting and lint rules so our code stays clean.
- **`ty`**: A static type checker that verifies our type annotations have no bugs before running the code.

---

## Part 2: How Our Project Works (File-by-File Walkthrough)

### High-Level Data Flow

```text
examples/example.cool
        │
        ▼
  cli.py: main()           <-- Gets file path from CLI arg or "Read which file? "
        │
        ▼
  lexer.py: tokenize_file() <-- Reads file (stripping UTF-8 BOM with "utf-8-sig")
        │
        ▼
  lexer.py: tokenize()     <-- Loops through text with TOKEN_REGEX.match(source, pos)
        │                      Creates Token(...) objects or raises LexicalError(line, ...)
        ▼
  lexer.py: format_tokens() <-- Formats each token as: TYPE "lexeme" [line N]
        │                       Appends: Done reading tokens
        ▼
  Printed to terminal
```

---

### File 1: `src/cool_lexer/tokens.py` (The Data Blueprints)

This file defines **what a token looks like** and **what an error looks like**:

1. **`TokenType(StrEnum)`**: Lists all 17 legal token names in COOL:
   - Keywords: `FUNC`, `IF`, `THEN`, `ELSE`, `TRUE`, `FALSE`
   - Identifiers & literals: `IDENTIFIER`, `INT_LITERAL`, `STRING_LITERAL`
   - Punctuation & assignment: `LPAREN`, `RPAREN`, `COMMA`, `ASSIGN`, `LBRACE`, `RBRACE`, `SEMICOLON`
   - End of file: `END_OF_INPUT`
2. **`KEYWORDS`**: A dictionary mapping the 6 lowercase keyword strings (`"func"`, `"if"`, `"then"`, `"else"`, `"true"`, `"false"`) to their `TokenType`.
3. **`Token(BaseModel)`**: A frozen Pydantic model with three fields:
   - `type: TokenType`
   - `lexeme: str`
   - `line: int = Field(ge=1)` (must be 1 or greater)
   - `.format()` returns the exact assignment string: `f'{self.type.value} "{self.lexeme}" [line {self.line}]'`
4. **`LexicalError(Exception)`**: Raised the instant invalid input is seen. It stores `line`, `lexeme`, and `message` so the CLI can print the line number and abort.

---

### File 2: `src/cool_lexer/lexer.py` (The Brain)

Instead of running 15 separate regex searches at every position, we combine all rules into **one master regex** (`TOKEN_REGEX`) using `|` (OR) and named groups `(?P<NAME>...)`.

At index `pos = 0`, we call `TOKEN_REGEX.match(source, pos)`:
- `.match(source, pos)` checks **only at the exact current position `pos`** (it never skips ahead).
- Whichever rule matches advances `pos = match.end()`.
- We repeat until `pos == len(source)`, then append `END_OF_INPUT "" [line N]`.

#### Why the Order of `_TOKEN_SPECS` Is Critical!

Python's `|` operator is **first-match wins** (left to right). If you change the order of rules in `_TOKEN_SPECS`, things break:

| Rule # | Name | Pattern | Why it MUST be in this exact position |
| :---: | :--- | :--- | :--- |
| 1 | `NEWLINE` | `\r\n\|\r\|\n` | `\r\n` (Windows) must come before `\r` and `\n` so a Windows newline counts as **1 line**, not 2. |
| 2 | `WHITESPACE` | `[ \t]+` | Skips spaces and tabs without emitting any token. |
| 3 | `COMMENT` | `//[^\r\n]*` | **Must come BEFORE `OPERATOR` (`/`)!** Otherwise `// hello` would be lexed as two divide operators `/` and `/`. |
| 4 | `STRING_LITERAL` | `"[^"\r\n]*"` | Matches a complete single-line string. We slice `raw[1:-1]` to strip the outer quotes per the spec. |
| 5 | `UNTERMINATED_STRING` | `"[^"\r\n]*` | **Must come AFTER `STRING_LITERAL`!** If a quote opens and hits a newline or EOF before closing, this catches it and raises `LexicalError`. |
| 6 | `ASSIGN` | `::=` | Matches the 3-character assignment operator. (`::` alone is invalid and falls through to `MISMATCH`.) |
| 7 | `INT_LITERAL` | `-?[0-9]+` | **Must come BEFORE `OPERATOR` (`-`)!** Otherwise `-5` would be lexed as `IDENTIFIER "-"` + `INT_LITERAL "5"`. Meanwhile `-(n, 1)` has `(` after `-`, so `INT_LITERAL` fails and `OPERATOR` catches `-`. |
| 8 | `WORD` | `[A-Za-z]+` | Matches a whole word greedily, then checks `KEYWORDS.get(raw, TokenType.IDENTIFIER)`. |
| 9 | `OPERATOR` | `==\|!=\|>=\|<=\|[+\-*/=><]` | **2-char operators (`==`, `!=`, `>=`, `<=`) MUST come BEFORE 1-char operators (`=`, `>`, `<`)!** Otherwise `>=` would be lexed as `>` followed by `=`. Also notice `!` alone is NOT in `[+\-*/=><]`, so `!` alone is an error. |
| 10–15 | `LPAREN` .. `SEMICOLON` | `\(`, `\)`, `,`, `\{`, `\}`, `;` | Single-character punctuation. |
| 16 | `MISMATCH` | `.` | **Must be LAST!** Catches any illegal character (like `@`, `!`, `:`, `_`, `$`) and immediately raises `LexicalError`. |

#### The `iffy` Problem (Why `WORD` + `KEYWORDS.get()` is smart)
Suppose the input is `iffy`.
- If you put `IF` (`if`) as a separate regex rule before `IDENTIFIER`, `IF` would match `"if"` and leave `"fy"` as `IDENTIFIER "fy"` — **WRONG!**
- Because `WORD` matches `[A-Za-z]+` greedily first, it grabs the entire `"iffy"`. Then `KEYWORDS.get("iffy", TokenType.IDENTIFIER)` sees `"iffy"` is not in `KEYWORDS`, so it emits `IDENTIFIER "iffy"`.

---

### File 3: `src/cool_lexer/cli.py` (The User Interface)

1. Checks `sys.argv`:
   - If you run `uv run cool-lexer examples/example.cool`, it uses `examples/example.cool`.
   - If you run `uv run cool-lexer` with no arguments, it prints `Read which file? ` and waits for input (matching the assignment sample).
2. Calls `tokenize_file(Path(file_path))`.
3. Handles errors cleanly without crashing with ugly Python tracebacks:
   - `FileNotFoundError`, `OSError`, `UnicodeDecodeError`, `EOFError`/`KeyboardInterrupt`, and `LexicalError` all print a clear message and exit with code `1`.

---

### Trace of `examples/example.cool`

Input file (6 lines + trailing newline at end of line 6):
```text
1: fact ::= func(n)
2:   {
3:     if =(n, 1)
4:       then 1
5:       else *(n, fact(-(n, 1)));
6:   };
7: (empty line after final \n)
```

Key moments in the trace:
- Line 1: `fact` → `WORD` (not in `KEYWORDS`) → `IDENTIFIER "fact" [line 1]`. `::=` → `ASSIGN "::=" [line 1]`. `func` → `WORD` (in `KEYWORDS`) → `FUNC "func" [line 1]`.
- Line 3: `=` → `OPERATOR` → `IDENTIFIER "=" [line 3]`.
- Line 5: `-(n, 1)` → at `-`, `INT_LITERAL` fails because `(` is not a digit, so `OPERATOR` matches `-` → `IDENTIFIER "-" [line 5]`.
- Line 6 → Line 7: the `\n` after `;` increments `line` from `6` to `7`, then the loop ends and emits `END_OF_INPUT "" [line 7]`, followed by `Done reading tokens`.

---

## Part 3: How to Pass the Viva (Q&A Script)

Read these out loud before the viva. If you can answer these in your own words, you will pass comfortably.

### Q1: What is the difference between a token and a lexeme?
**Answer:** "A **lexeme** is the exact characters from the source file, like `fact` or `1`. A **token** is the category label we assign to that lexeme, like `IDENTIFIER` or `INT_LITERAL`."

### Q2: Why did you choose Python instead of Flex?
**Answer:** "The assignment allows either Flex or a hand-written regex scanner in Python. In Python, we used a single compiled master regex (`re.compile`) with named groups and `.match(source, pos)` so we have full control over rule priority, line tracking, and clean error reporting, without Windows C-toolchain issues."

### Q3: How does your lexer enforce Longest Match (Maximal Munch)?
**Answer:** "Two ways: first, quantifiers like `[A-Za-z]+` and `[0-9]+` are greedy, so `iffy` is read as one whole word before checking `KEYWORDS`. Second, in our alternation, multi-character tokens like `//`, `::=`, `-?[0-9]+`, and `>=` are placed **before** single-character tokens like `/`, `-`, and `>`."

### Q4: What happens if you put `OPERATOR` (`/`) before `COMMENT` (`//...`)?
**Answer:** "Python's `re` alternation is first-match wins. If `/` came first, a comment `// hello` would match `/` as an `IDENTIFIER`, then another `/`, and then `hello` as an `IDENTIFIER` instead of ignoring the comment."

### Q5: How do you distinguish negative numbers like `-5` from subtraction like `-(n, 1)`?
**Answer:** "`INT_LITERAL` (`-?[0-9]+`) is placed before `OPERATOR` (`-`). If `-` is immediately followed by digits, `INT_LITERAL` matches `-5`. If `-` is followed by `(` or a space, `INT_LITERAL` does not match, so it falls through to `OPERATOR` and emits `IDENTIFIER "-"`."

### Q6: What is a known edge case of `-?[0-9]+`?
**Answer:** "In `x-1` with no spaces, a stateless lexer matches `x` (`IDENTIFIER`) and `-1` (`INT_LITERAL`). That's expected for COOL because COOL uses prefix notation like `-(n, 1)`."

### Q7: Why are operators like `+`, `-`, `==`, `>=` labeled `IDENTIFIER`?
**Answer:** "Because the COOL assignment spec explicitly defines `Identifier` as a sequence of letters (`A-Z`, `a-z`) OR operator symbols (`+ - * / = > >= < <= == !=`), and the sample output prints `IDENTIFIER "="` and `IDENTIFIER "*"`."

### Q8: How do you handle keywords vs identifiers?
**Answer:** "The `WORD` rule matches `[A-Za-z]+`, and then we look up the matched string in `KEYWORDS`. If it's one of `func`, `if`, `then`, `else`, `true`, `false`, we emit its keyword token (like `FUNC`); otherwise we emit `IDENTIFIER`. Case matters—`FUNC` is an `IDENTIFIER`, not `func`."

### Q9: How do you handle quoted strings and multi-line strings?
**Answer:** "`STRING_LITERAL` matches `\"[^\"\\r\\n]*\"` and strips the surrounding quotes with `raw[1:-1]`. Because `\\r` and `\\n` are excluded, a string cannot span multiple lines. If a quote opens without closing before a newline or EOF, `UNTERMINATED_STRING` catches it and raises `LexicalError` with that line number."

### Q10: What happens when the input has an invalid character like `@` or `!`?
**Answer:** "Every valid rule fails at that position, so the final catch-all rule `MISMATCH` (`.`) matches that character and raises `LexicalError`, printing the line number and aborting immediately."

### Q11: Why does `END_OF_INPUT` say `[line 7]` on a 6-line file?
**Answer:** "Because line 6 ends with a newline (`\\n`), which increments the `line` counter to `7` right before the loop reaches the end of the file."

### Q12: Why does `tokenize_file` use `encoding="utf-8-sig"`?
**Answer:** "On Windows, editors like Notepad sometimes save a hidden UTF-8 BOM (`\\ufeff`) at the start of a file. `utf-8-sig` strips that BOM automatically so it doesn't cause a false lexical error on line 1."

---

### 15-Minute Before-Viva Checklist
1. Pull the latest repo and run `uv sync`.
2. Run `uv run pytest -v` and verify all **28 tests pass**.
3. Run `uv run cool-lexer examples/example.cool` and confirm it ends with `END_OF_INPUT "" [line 7]` and `Done reading tokens`.
4. Run `uv run cool-lexer` (no args) and type `examples/example.cool` at the `Read which file? ` prompt to verify interactive mode.
5. Keep `src/cool_lexer/lexer.py` open in your editor—90% of viva questions will point directly at `_TOKEN_SPECS` and `tokenize()`.
