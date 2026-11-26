import re
from pathlib import Path

from cool_lexer.tokens import KEYWORDS, LexicalError, Token, TokenType

_TOKEN_SPECS: list[tuple[str, str]] = [
    ("NEWLINE", r"\r\n|\r|\n"),
    ("WHITESPACE", r"[ \t]+"),
    ("COMMENT", r"//[^\r\n]*"),
    ("STRING_LITERAL", r'"[^"\r\n]*"'),
    ("UNTERMINATED_STRING", r'"[^"\r\n]*'),
    ("ASSIGN", r"::="),
    ("INT_LITERAL", r"-?[0-9]+"),
    ("WORD", r"[A-Za-z]+"),
    ("OPERATOR", r"==|!=|>=|<=|[+\-*/=><]"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("SEMICOLON", r";"),
    ("MISMATCH", r"."),
]

TOKEN_REGEX: re.Pattern[str] = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in _TOKEN_SPECS)
)

_SIMPLE_TOKEN_TYPES: dict[str, TokenType] = {
    "ASSIGN": TokenType.ASSIGN,
    "INT_LITERAL": TokenType.INT_LITERAL,
    "OPERATOR": TokenType.IDENTIFIER,
    "LPAREN": TokenType.LPAREN,
    "RPAREN": TokenType.RPAREN,
    "COMMA": TokenType.COMMA,
    "LBRACE": TokenType.LBRACE,
    "RBRACE": TokenType.RBRACE,
    "SEMICOLON": TokenType.SEMICOLON,
}


def tokenize(source: str) -> list[Token]:
    """Scan COOL source text and return its token stream ending with END_OF_INPUT."""
    tokens: list[Token] = []
    line = 1
    pos = 0
    length = len(source)

    while pos < length:
        match = TOKEN_REGEX.match(source, pos)
        if match is None:
            raise LexicalError(line=line, lexeme=source[pos], message="Unexpected character")

        kind = match.lastgroup
        raw = match.group()
        pos = match.end()

        if kind == "NEWLINE":
            line += 1
        elif kind in ("WHITESPACE", "COMMENT"):
            continue
        elif kind == "STRING_LITERAL":
            tokens.append(Token(type=TokenType.STRING_LITERAL, lexeme=raw[1:-1], line=line))
        elif kind == "UNTERMINATED_STRING":
            raise LexicalError(line=line, lexeme=raw, message="Unterminated string literal")
        elif kind == "WORD":
            token_type = KEYWORDS.get(raw, TokenType.IDENTIFIER)
            tokens.append(Token(type=token_type, lexeme=raw, line=line))
        elif kind == "MISMATCH":
            raise LexicalError(line=line, lexeme=raw, message="Unexpected character")
        elif kind is not None and kind in _SIMPLE_TOKEN_TYPES:
            tokens.append(Token(type=_SIMPLE_TOKEN_TYPES[kind], lexeme=raw, line=line))
        else:
            raise RuntimeError(f"Unhandled token kind: {kind!r}")

    tokens.append(Token(type=TokenType.END_OF_INPUT, lexeme="", line=line))
    return tokens


def tokenize_file(path: Path) -> list[Token]:
    """Read a COOL source file and tokenize its contents."""
    return tokenize(path.read_text(encoding="utf-8-sig"))


def format_tokens(tokens: list[Token]) -> str:
    """Format a token list into the assignment's expected output text."""
    lines = [token.format() for token in tokens]
    lines.append("Done reading tokens")
    return "\n".join(lines)
