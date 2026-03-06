"""Translate English error messages to the configured target language.

Translation strategy (in priority order):
1. Built-in dictionary for common error patterns (fast, no API key needed)
2. AI-powered translation if an AI provider is configured

The target language is set once when constructing ErrorTranslator and applied
to every error message automatically.
"""

from __future__ import annotations
import re
from typing import Optional
from error_translator.models import Language


# ── Built-in translation dictionary ─────────────────────────────────────────
# Format: { Language: { pattern_or_exact: translation } }
# Patterns are matched case-insensitively as substrings.
_BUILTIN: dict[Language, dict[str, str]] = {
    Language.JA: {
        # Python
        "name '(.+)' is not defined": "名前 '{0}' が定義されていません",
        "cannot import name '(.+)'": "'{0}' をインポートできません",
        "no module named '(.+)'": "モジュール '{0}' が見つかりません",
        "list index out of range": "リストのインデックスが範囲外です",
        "dict has no key": "辞書にキーが存在しません",
        "key error": "キーエラー：指定したキーが辞書に存在しません",
        "index error": "インデックスエラー：範囲外のインデックスにアクセスしました",
        "type error": "型エラー：不正な型が使用されました",
        "value error": "値エラー：不正な値が使用されました",
        "attribute error": "属性エラー：オブジェクトにその属性が存在しません",
        "zero division": "ゼロ除算エラー：0 で割ることはできません",
        "file not found": "ファイルが見つかりません",
        "permission denied": "アクセス権限がありません",
        "syntax error": "構文エラー：コードの書き方が正しくありません",
        "indentation error": "インデントエラー：インデントが正しくありません",
        "recursion error": "再帰エラー：再帰の深さが上限を超えました",
        "memory error": "メモリエラー：メモリが不足しています",
        "overflow error": "オーバーフローエラー：数値が大きすぎます",
        "timeout": "タイムアウト：処理時間が上限を超えました",
        "connection refused": "接続が拒否されました",
        "connection reset": "接続がリセットされました",
        # JavaScript / TypeScript
        "cannot read propert": "undefined または null のプロパティを読み取れません",
        "is not a function": "関数ではありません",
        "is not defined": "定義されていません",
        "unexpected token": "予期しないトークンがあります",
        "cannot set propert": "プロパティを設定できません",
        "maximum call stack": "コールスタックの上限を超えました（無限再帰の可能性）",
        "promise rejection": "Promise が拒否されました",
        "fetch failed": "ネットワークリクエストが失敗しました",
        # Java
        "nullpointerexception": "NullPointerException：null オブジェクトにアクセスしました",
        "arrayindexoutofbounds": "配列のインデックスが範囲外です",
        "classnotfoundexception": "クラスが見つかりません",
        "classcastexception": "型キャストエラー：互換性のない型に変換しようとしました",
        "stackoverflowerror": "スタックオーバーフロー：再帰が深すぎます",
        "outofmemoryerror": "メモリ不足エラー",
        "illegalargumentexception": "不正な引数が渡されました",
        "illegalstateexception": "オブジェクトが不正な状態です",
        "unsupportedoperationexception": "サポートされていない操作です",
        "concurrentmodificationexception": "イテレーション中にコレクションが変更されました",
    },
    Language.EN: {},  # source language — no translation needed
}


def _apply_pattern(pattern: str, template: str, message: str) -> Optional[str]:
    """Try regex match and fill template groups."""
    m = re.search(pattern, message, re.IGNORECASE)
    if m:
        try:
            groups = m.groups()
            return template.format(*groups)
        except IndexError:
            return template
    return None


class ErrorMessageTranslator:
    """Translate English error messages to a target language."""

    def __init__(self, target_lang: Language = Language.JA) -> None:
        self.target_lang = target_lang
        self._dict = _BUILTIN.get(target_lang, {})

    def translate(self, message: str) -> str:
        """
        Translate *message* (English) to the configured target language.

        Returns the translated string. Falls back to the original message
        if no match is found and no AI provider is available.
        """
        if self.target_lang == Language.EN:
            return message

        msg_lower = message.lower()

        for pattern, translation in self._dict.items():
            # Pattern contains regex groups → try regex match
            if "(" in pattern:
                result = _apply_pattern(pattern, translation, message)
                if result:
                    return result
            # Plain substring match
            elif pattern.lower() in msg_lower:
                return translation

        # No match found — return original
        return message

    def add_translation(self, pattern: str, translation: str) -> None:
        """Register a custom translation entry at runtime."""
        self._dict[pattern] = translation
