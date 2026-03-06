"""Main ErrorTranslator — orchestrates detection, translation, and AI advice."""

from __future__ import annotations
from typing import Optional

from error_translator.models import ErrorAnalysis, Language, ErrorLanguage
from error_translator.detectors import ErrorDetector
from error_translator.translators import ErrorMessageTranslator
from error_translator.ai_advisor import AIAdvisor, get_advisor


class ErrorTranslator:
    """
    All-in-one error analyzer.

    Parameters
    ----------
    target_lang:
        Language to translate error messages into. Default: "ja" (Japanese).
        Accepts Language enum or string ("ja", "en").
    ai_provider:
        "anthropic" or "openai". If None, auto-detected from environment variables
        (ANTHROPIC_API_KEY or OPENAI_API_KEY).
    ai_api_key:
        Explicit API key. Falls back to environment variable if not provided.
    ai_model:
        Override the default AI model (e.g. "gpt-4o", "claude-opus-4-6").
    enable_ai:
        Set to False to disable AI advice entirely. Default: True.

    Examples
    --------
    Basic usage (Japanese translation + AI advice from env var):

        from error_translator import ErrorTranslator

        et = ErrorTranslator(target_lang="ja")
        result = et.analyze("TypeError: Cannot read properties of undefined (reading 'map')")
        print(result)

    Explicit provider:

        et = ErrorTranslator(
            target_lang="ja",
            ai_provider="openai",
            ai_api_key="sk-...",
        )

    No AI (translation only):

        et = ErrorTranslator(target_lang="ja", enable_ai=False)
    """

    def __init__(
        self,
        target_lang: str | Language = Language.JA,
        ai_provider: Optional[str] = None,
        ai_api_key: Optional[str] = None,
        ai_model: Optional[str] = None,
        enable_ai: bool = True,
    ) -> None:
        self.target_lang = Language(target_lang) if isinstance(target_lang, str) else target_lang

        self._detector = ErrorDetector()
        self._translator = ErrorMessageTranslator(target_lang=self.target_lang)

        self._advisor: Optional[AIAdvisor] = None
        if enable_ai:
            self._advisor = get_advisor(
                provider=ai_provider,
                api_key=ai_api_key,
                model=ai_model,
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def analyze(self, raw_error: str) -> ErrorAnalysis:
        """
        Fully analyze an error string.

        Steps:
            1. Strip ANSI codes and clean stack traces
            2. Detect programming language
            3. Extract error type and core message
            4. Translate the message (English → target_lang)
            5. Fetch AI advice (if provider is configured)

        Returns an ErrorAnalysis object.
        """
        # 1–3: detect & clean
        detected = self._detector.detect(raw_error)

        # 4: translate
        translated = self._translator.translate(detected["error_message"])

        # 5: AI advice
        advice: Optional[str] = None
        provider_name: Optional[str] = None
        if self._advisor:
            try:
                advice = self._advisor.advise(
                    error_message=detected["error_message"],
                    error_language=detected["error_language"],
                    error_type=detected["error_type"],
                    target_lang=self.target_lang,
                )
                provider_name = self._advisor.provider
            except Exception as e:
                advice = f"[AI advice unavailable: {e}]"

        return ErrorAnalysis(
            raw_error=raw_error,
            clean_error=detected["clean_error"],
            error_language=detected["error_language"],
            error_type=detected["error_type"],
            error_message=detected["error_message"],
            translated_message=translated if translated != detected["error_message"] else None,
            target_lang=self.target_lang,
            ai_advice=advice,
            ai_provider=provider_name,
        )

    def translate_only(self, raw_error: str) -> str:
        """Detect and translate without calling AI."""
        detected = self._detector.detect(raw_error)
        return self._translator.translate(detected["error_message"])

    def add_translation(self, pattern: str, translation: str) -> None:
        """Add a custom translation pattern for the current target language."""
        self._translator.add_translation(pattern, translation)
