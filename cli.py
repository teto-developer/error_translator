"""CLI for error-translator.

Usage:
    # Pipe an error
    python -m pytest 2>&1 | error-translator

    # Pass directly
    error-translator "TypeError: Cannot read properties of undefined"

    # Specify language
    error-translator --lang ja "NameError: name 'foo' is not defined"

    # Disable AI
    error-translator --no-ai "IndexError: list index out of range"
"""

from __future__ import annotations
import argparse
import sys
from error_translator.core import ErrorTranslator
from error_translator.models import Language


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="error-translator",
        description="Detect, translate, and get AI advice for error messages.",
    )
    parser.add_argument(
        "error",
        nargs="?",
        help="Error message or stack trace. Reads from stdin if not provided.",
    )
    parser.add_argument(
        "--lang",
        default="ja",
        choices=[l.value for l in Language],
        help="Target language for translation (default: ja)",
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default=None,
        help="AI provider (auto-detected from env if not set)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override AI model name",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI advice",
    )
    args = parser.parse_args()

    # Read error text
    if args.error:
        raw = args.error
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
    else:
        parser.print_help()
        sys.exit(1)

    et = ErrorTranslator(
        target_lang=args.lang,
        ai_provider=args.provider,
        ai_model=args.model,
        enable_ai=not args.no_ai,
    )

    result = et.analyze(raw)

    # Pretty output
    sep = "─" * 60
    print(sep)
    print(f"  Language : {result.error_language.value}")
    print(f"  Type     : {result.error_type or 'Unknown'}")
    print(f"  Original : {result.error_message}")
    if result.translated_message:
        print(f"  翻訳     : {result.translated_message}")
    if result.ai_advice:
        print(sep)
        print("  AI Advice")
        print(sep)
        for line in result.ai_advice.splitlines():
            print(f"  {line}")
    print(sep)


if __name__ == "__main__":
    main()
