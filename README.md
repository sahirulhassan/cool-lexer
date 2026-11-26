# cool-lexer

A regex-based **lexical analyzer (scanner)** for the **COOL (Classroom Object Oriented Language)** written in Python for **CSC-303 (Compiler Construction, Fall 2026)**.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) (Python 3.12+).

```powershell
# Install dependencies
uv sync

# Run on the sample COOL file
uv run cool-lexer examples/example.cool

# Run interactively (prompts: "Read which file? ")
uv run cool-lexer
```

## Development & Verification

```powershell
# Run tests (28 test cases)
uv run pytest -v

# Lint & format check
uv run ruff check .
uv run ruff format --check .

# Type check
uv run ty check
```

## Project Layout

```text
├── examples/
│   └── example.cool          # Factorial sample from the assignment
├── src/cool_lexer/
│   ├── __init__.py           # Public package exports
│   ├── __main__.py           # Enables `python -m cool_lexer`
│   ├── cli.py                # CLI & interactive "Read which file?" prompt
│   ├── lexer.py              # Master regex scanner & line tracker
│   └── tokens.py             # TokenType enum, Pydantic Token model, LexicalError
├── tests/
│   └── test_lexer.py         # Unit & CLI tests
├── pyproject.toml            # Project config (uv, ruff, pytest)
└── VIVA_GUIDE.md             # Zero-jargon study guide & viva Q&A for teammates
```

## Study & Viva Prep

New to compilers or regexes? Read **[VIVA_GUIDE.md](VIVA_GUIDE.md)**—it explains all prerequisite concepts, walks through every file in plain English, and gives ready-to-use answers for the viva.
