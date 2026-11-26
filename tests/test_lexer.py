from io import StringIO
from pathlib import Path

import pytest
from pydantic import ValidationError

from cool_lexer import LexicalError, Token, TokenType, format_tokens, tokenize, tokenize_file
from cool_lexer.cli import main

EXPECTED_EXAMPLE_OUTPUT = """\
IDENTIFIER "fact" [line 1]
ASSIGN "::=" [line 1]
FUNC "func" [line 1]
LPAREN "(" [line 1]
IDENTIFIER "n" [line 1]
RPAREN ")" [line 1]
LBRACE "{" [line 2]
IF "if" [line 3]
IDENTIFIER "=" [line 3]
LPAREN "(" [line 3]
IDENTIFIER "n" [line 3]
COMMA "," [line 3]
INT_LITERAL "1" [line 3]
RPAREN ")" [line 3]
THEN "then" [line 4]
INT_LITERAL "1" [line 4]
ELSE "else" [line 5]
IDENTIFIER "*" [line 5]
LPAREN "(" [line 5]
IDENTIFIER "n" [line 5]
COMMA "," [line 5]
IDENTIFIER "fact" [line 5]
LPAREN "(" [line 5]
IDENTIFIER "-" [line 5]
LPAREN "(" [line 5]
IDENTIFIER "n" [line 5]
COMMA "," [line 5]
INT_LITERAL "1" [line 5]
RPAREN ")" [line 5]
RPAREN ")" [line 5]
RPAREN ")" [line 5]
SEMICOLON ";" [line 5]
RBRACE "}" [line 6]
SEMICOLON ";" [line 6]
END_OF_INPUT "" [line 7]
Done reading tokens"""


def test_example_cool_matches_assignment_output() -> None:
    example_path = Path(__file__).resolve().parent.parent / "examples" / "example.cool"
    tokens = tokenize_file(example_path)
    assert format_tokens(tokens) == EXPECTED_EXAMPLE_OUTPUT


def test_keywords_and_identifier_prefixes() -> None:
    tokens = tokenize("func if then else true false iffy trueish functional")
    assert [(t.type, t.lexeme) for t in tokens[:-1]] == [
        (TokenType.FUNC, "func"),
        (TokenType.IF, "if"),
        (TokenType.THEN, "then"),
        (TokenType.ELSE, "else"),
        (TokenType.TRUE, "true"),
        (TokenType.FALSE, "false"),
        (TokenType.IDENTIFIER, "iffy"),
        (TokenType.IDENTIFIER, "trueish"),
        (TokenType.IDENTIFIER, "functional"),
    ]


def test_operators_as_identifiers() -> None:
    tokens = tokenize("+ - * / = > >= < <= == !=")
    assert [(t.type, t.lexeme) for t in tokens[:-1]] == [
        (TokenType.IDENTIFIER, "+"),
        (TokenType.IDENTIFIER, "-"),
        (TokenType.IDENTIFIER, "*"),
        (TokenType.IDENTIFIER, "/"),
        (TokenType.IDENTIFIER, "="),
        (TokenType.IDENTIFIER, ">"),
        (TokenType.IDENTIFIER, ">="),
        (TokenType.IDENTIFIER, "<"),
        (TokenType.IDENTIFIER, "<="),
        (TokenType.IDENTIFIER, "=="),
        (TokenType.IDENTIFIER, "!="),
    ]


def test_integers_and_minus_operator() -> None:
    tokens = tokenize("0 42 -7 -(n, 1)")
    assert [(t.type, t.lexeme) for t in tokens[:-1]] == [
        (TokenType.INT_LITERAL, "0"),
        (TokenType.INT_LITERAL, "42"),
        (TokenType.INT_LITERAL, "-7"),
        (TokenType.IDENTIFIER, "-"),
        (TokenType.LPAREN, "("),
        (TokenType.IDENTIFIER, "n"),
        (TokenType.COMMA, ","),
        (TokenType.INT_LITERAL, "1"),
        (TokenType.RPAREN, ")"),
    ]


def test_quoted_strings_strip_quotes_and_preserve_spaces_and_tabs() -> None:
    tokens = tokenize('"hello,\tI am a quoted string" ""')
    assert [(t.type, t.lexeme) for t in tokens[:-1]] == [
        (TokenType.STRING_LITERAL, "hello,\tI am a quoted string"),
        (TokenType.STRING_LITERAL, ""),
    ]


def test_comments_ignored_and_slash_preserved() -> None:
    source = "// full line comment\nx / y // inline comment\n"
    tokens = tokenize(source)
    assert [(t.type, t.lexeme, t.line) for t in tokens] == [
        (TokenType.IDENTIFIER, "x", 2),
        (TokenType.IDENTIFIER, "/", 2),
        (TokenType.IDENTIFIER, "y", 2),
        (TokenType.END_OF_INPUT, "", 3),
    ]


@pytest.mark.parametrize(
    ("source", "expected_line"),
    [
        ("x @ y", 1),
        ("x\n!\ny", 2),
        ("x ::= 1\n:\n", 2),
        ('"unterminated', 1),
        ('ok\n"multi\nline"', 2),
    ],
)
def test_lexical_errors_abort_with_line_number(source: str, expected_line: int) -> None:
    with pytest.raises(LexicalError) as exc_info:
        tokenize(source)
    assert exc_info.value.line == expected_line


def test_cli_with_argument(capsys: pytest.CaptureFixture[str]) -> None:
    example_path = Path(__file__).resolve().parent.parent / "examples" / "example.cool"
    exit_code = main([str(example_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == EXPECTED_EXAMPLE_OUTPUT


def test_cli_interactive_prompt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    sample = tmp_path / "sample.cool"
    sample.write_text('true "ok"\n', encoding="utf-8")
    monkeypatch.setattr("sys.stdin", StringIO(f"{sample}\n"))

    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Read which file? " in captured.out
    assert 'TRUE "true" [line 1]' in captured.out
    assert 'STRING_LITERAL "ok" [line 1]' in captured.out
    assert 'END_OF_INPUT "" [line 2]' in captured.out


def test_cli_aborts_on_lexical_error(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    bad_file = tmp_path / "bad.cool"
    bad_file.write_text("ok\nbad @ token\n", encoding="utf-8")

    exit_code = main([str(bad_file)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "line 2" in captured.out


@pytest.mark.parametrize("source", ["", "   \t  ", "// comment at EOF without newline"])
def test_empty_whitespace_and_eof_comment(source: str) -> None:
    tokens = tokenize(source)
    assert [(t.type, t.lexeme, t.line) for t in tokens] == [
        (TokenType.END_OF_INPUT, "", 1),
    ]


@pytest.mark.parametrize("newline", ["\r\n", "\r"])
def test_crlf_and_cr_line_endings(newline: str) -> None:
    source = f"x ::= 1{newline}// comment{newline}y"
    tokens = tokenize(source)
    assert [(t.type, t.lexeme, t.line) for t in tokens] == [
        (TokenType.IDENTIFIER, "x", 1),
        (TokenType.ASSIGN, "::=", 1),
        (TokenType.INT_LITERAL, "1", 1),
        (TokenType.IDENTIFIER, "y", 3),
        (TokenType.END_OF_INPUT, "", 3),
    ]


def test_keyword_case_sensitivity() -> None:
    tokens = tokenize("FUNC If True FALSE")
    assert [(t.type, t.lexeme) for t in tokens[:-1]] == [
        (TokenType.IDENTIFIER, "FUNC"),
        (TokenType.IDENTIFIER, "If"),
        (TokenType.IDENTIFIER, "True"),
        (TokenType.IDENTIFIER, "FALSE"),
    ]


def test_negative_integer_and_adjacent_operator_edge_cases() -> None:
    tokens = tokenize("-0 - 5 --5 x-1 === !== /*")
    assert [(t.type, t.lexeme) for t in tokens[:-1]] == [
        (TokenType.INT_LITERAL, "-0"),
        (TokenType.IDENTIFIER, "-"),
        (TokenType.INT_LITERAL, "5"),
        (TokenType.IDENTIFIER, "-"),
        (TokenType.INT_LITERAL, "-5"),
        (TokenType.IDENTIFIER, "x"),
        (TokenType.INT_LITERAL, "-1"),
        (TokenType.IDENTIFIER, "=="),
        (TokenType.IDENTIFIER, "="),
        (TokenType.IDENTIFIER, "!="),
        (TokenType.IDENTIFIER, "="),
        (TokenType.IDENTIFIER, "/"),
        (TokenType.IDENTIFIER, "*"),
    ]


def test_partial_assign_double_colon_raises_lexical_error() -> None:
    with pytest.raises(LexicalError) as exc_info:
        tokenize("x ::= 1\n::\n")
    assert exc_info.value.line == 2


def test_tokenize_file_handles_utf8_bom(tmp_path: Path) -> None:
    bom_file = tmp_path / "bom.cool"
    bom_file.write_bytes(b"\xef\xbb\xbffunc\n")
    tokens = tokenize_file(bom_file)
    assert [(t.type, t.lexeme, t.line) for t in tokens] == [
        (TokenType.FUNC, "func", 1),
        (TokenType.END_OF_INPUT, "", 2),
    ]


def test_cli_missing_file_returns_nonzero(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    missing = tmp_path / "missing.cool"
    exit_code = main([str(missing)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "file not found" in captured.out


def test_cli_empty_prompt_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin", StringIO("\n"))
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no file path provided" in captured.out


def test_cli_eof_on_prompt_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin", StringIO(""))
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "input cancelled" in captured.out


def test_cli_directory_and_invalid_utf8_return_nonzero(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    assert main([str(tmp_path)]) == 1
    assert "unable to read file" in capsys.readouterr().out

    binary_file = tmp_path / "binary.cool"
    binary_file.write_bytes(b"\xff\xfe\x00\x80")
    assert main([str(binary_file)]) == 1
    assert "not valid UTF-8" in capsys.readouterr().out


def test_token_pydantic_validation_and_immutability() -> None:
    with pytest.raises(ValidationError):
        Token(type=TokenType.IDENTIFIER, lexeme="x", line=0)

    token = Token(type=TokenType.IDENTIFIER, lexeme="x", line=1)
    with pytest.raises(ValidationError):
        token.lexeme = "y"  # ty: ignore[invalid-assignment]
