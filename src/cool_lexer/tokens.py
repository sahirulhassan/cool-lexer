from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TokenType(StrEnum):
    """All token types recognized by the COOL lexical analyzer."""

    # Keywords
    FUNC = "FUNC"
    IF = "IF"
    THEN = "THEN"
    ELSE = "ELSE"
    TRUE = "TRUE"
    FALSE = "FALSE"

    # Identifiers and literals
    IDENTIFIER = "IDENTIFIER"
    INT_LITERAL = "INT_LITERAL"
    STRING_LITERAL = "STRING_LITERAL"

    # Punctuation and assignment
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    ASSIGN = "ASSIGN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    SEMICOLON = "SEMICOLON"

    # End of input
    END_OF_INPUT = "END_OF_INPUT"


KEYWORDS: dict[str, TokenType] = {
    "func": TokenType.FUNC,
    "if": TokenType.IF,
    "then": TokenType.THEN,
    "else": TokenType.ELSE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}


class Token(BaseModel):
    """A single lexical token with its type, matched lexeme, and 1-based line number."""

    model_config = ConfigDict(frozen=True)

    type: TokenType
    lexeme: str
    line: int = Field(ge=1)

    def format(self) -> str:
        """Format token using the assignment's output representation."""
        return f'{self.type.value} "{self.lexeme}" [line {self.line}]'


class LexicalError(Exception):
    """Raised when the lexer encounters invalid input and must abort."""

    def __init__(self, line: int, lexeme: str, message: str) -> None:
        self.line = line
        self.lexeme = lexeme
        self.message = message
        super().__init__(str(self))

    def __str__(self) -> str:
        return f"Lexical error on line {self.line}: {self.message} ({self.lexeme!r})"
