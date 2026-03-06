"""AI-powered error advisor.

Supports:
  - Anthropic Claude  (pip install error-translator[anthropic])
  - OpenAI GPT        (pip install error-translator[openai])

The provider is selected automatically based on which API key is available,
or can be forced via the `provider` argument.
"""

from __future__ import annotations
import os
from typing import Optional
from error_translator.models import ErrorLanguage, Language


def _build_prompt(
    error_type: Optional[str],
    error_message: str,
    error_language: ErrorLanguage,
    target_lang: Language,
) -> str:
    lang_name = {"ja": "日本語", "en": "English"}.get(target_lang.value, target_lang.value)
    prog_lang = error_language.value.capitalize()

    return (
        f"You are an expert software debugger. "
        f"A developer encountered the following {prog_lang} error.\n\n"
        f"Error type: {error_type or 'Unknown'}\n"
        f"Error message: {error_message}\n\n"
        f"Please respond in {lang_name} with:\n"
        f"1. What this error means (1-2 sentences)\n"
        f"2. The most likely cause\n"
        f"3. How to fix it (concrete steps or example)\n"
        f"Be concise and practical."
    )


class AIAdvisor:
    """Fetch AI advice for an error."""

    def __init__(self, provider: str, api_key: str, model: Optional[str] = None) -> None:
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model

    def advise(
        self,
        error_message: str,
        error_language: ErrorLanguage = ErrorLanguage.GENERIC,
        error_type: Optional[str] = None,
        target_lang: Language = Language.JA,
    ) -> str:
        prompt = _build_prompt(error_type, error_message, error_language, target_lang)

        if self.provider == "anthropic":
            return self._call_anthropic(prompt)
        elif self.provider == "openai":
            return self._call_openai(prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider!r}. Use 'anthropic' or 'openai'.")

    # ── Anthropic ────────────────────────────────────────────────────────────
    def _call_anthropic(self, prompt: str) -> str:
        try:
            import anthropic  # type: ignore
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install error-translator[anthropic]"
            )
        client = anthropic.Anthropic(api_key=self.api_key)
        model = self.model or "claude-opus-4-6"
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    # ── OpenAI ───────────────────────────────────────────────────────────────
    def _call_openai(self, prompt: str) -> str:
        try:
            import openai  # type: ignore
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install error-translator[openai]"
            )
        client = openai.OpenAI(api_key=self.api_key)
        model = self.model or "gpt-4o-mini"
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""


def get_advisor(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[AIAdvisor]:
    """
    Auto-detect or explicitly create an AIAdvisor.

    Priority: explicit provider → ANTHROPIC_API_KEY env → OPENAI_API_KEY env
    Returns None if no API key is available.
    """
    if provider and api_key:
        return AIAdvisor(provider=provider, api_key=api_key, model=model)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if provider == "anthropic" and anthropic_key:
        return AIAdvisor(provider="anthropic", api_key=anthropic_key, model=model)
    if provider == "openai" and openai_key:
        return AIAdvisor(provider="openai", api_key=openai_key, model=model)

    # Auto-detect
    if anthropic_key:
        return AIAdvisor(provider="anthropic", api_key=anthropic_key, model=model)
    if openai_key:
        return AIAdvisor(provider="openai", api_key=openai_key, model=model)

    return None
