import sys
from pathlib import Path

from cool_lexer.lexer import format_tokens, tokenize_file
from cool_lexer.tokens import LexicalError


def main(argv: list[str] | None = None) -> int:
    """Run the COOL lexer CLI from an argument or interactive file prompt."""
    args = sys.argv[1:] if argv is None else argv
    if args:
        file_path = args[0]
    else:
        try:
            file_path = input("Read which file? ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nError: input cancelled.")
            return 1

    if not file_path:
        print("Error: no file path provided.")
        return 1

    try:
        tokens = tokenize_file(Path(file_path))
    except FileNotFoundError:
        print(f"Error: file not found: {file_path}")
        return 1
    except OSError as err:
        print(f"Error: unable to read file {file_path}: {err}")
        return 1
    except UnicodeDecodeError as err:
        print(f"Error: file is not valid UTF-8 ({file_path}): {err}")
        return 1
    except LexicalError as err:
        print(err)
        return 1

    print(format_tokens(tokens))
    return 0
