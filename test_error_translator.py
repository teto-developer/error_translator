"""Tests for error-translator."""

import pytest
from error_translator import ErrorTranslator, ErrorAnalysis, ErrorLanguage, Language
from error_translator.detectors import ErrorDetector
from error_translator.translators import ErrorMessageTranslator


# ── Detector tests ────────────────────────────────────────────────────────────

class TestErrorDetector:
    def setup_method(self):
        self.d = ErrorDetector()

    def test_python_traceback(self):
        raw = (
            "Traceback (most recent call last):\n"
            "  File 'main.py', line 5, in <module>\n"
            "    foo()\n"
            "NameError: name 'foo' is not defined"
        )
        r = self.d.detect(raw)
        assert r["error_language"] == ErrorLanguage.PYTHON
        assert r["error_type"] == "NameError"
        assert "foo" in r["error_message"]

    def test_python_index_error(self):
        r = self.d.detect("IndexError: list index out of range")
        assert r["error_language"] == ErrorLanguage.PYTHON
        assert r["error_type"] == "IndexError"

    def test_javascript_type_error(self):
        raw = (
            "TypeError: Cannot read properties of undefined (reading 'map')\n"
            "    at Array.map (<anonymous>)\n"
            "    at main.js:10:5"
        )
        r = self.d.detect(raw)
        assert r["error_language"] == ErrorLanguage.JAVASCRIPT
        assert r["error_type"] == "TypeError"

    def test_java_exception(self):
        raw = (
            "Exception in thread \"main\" java.lang.NullPointerException\n"
            "\tat com.example.Main.run(Main.java:20)\n"
            "\tat com.example.Main.main(Main.java:5)"
        )
        r = self.d.detect(raw)
        assert r["error_language"] == ErrorLanguage.JAVA
        assert "NullPointerException" in (r["error_type"] or "") or "NullPointerException" in r["error_message"]

    def test_ansi_stripped(self):
        raw = "\x1b[31mTypeError\x1b[0m: bad type"
        r = self.d.detect(raw)
        assert "\x1b" not in r["clean_error"]


# ── Translator tests ───────────────────────────────────────────────────────────

class TestTranslator:
    def setup_method(self):
        self.t = ErrorMessageTranslator(target_lang=Language.JA)

    def test_known_message(self):
        result = self.t.translate("list index out of range")
        assert "インデックス" in result or "範囲" in result

    def test_unknown_message_passthrough(self):
        msg = "some completely unknown error xyz123"
        assert self.t.translate(msg) == msg

    def test_regex_pattern(self):
        result = self.t.translate("name 'my_var' is not defined")
        assert "my_var" in result

    def test_en_passthrough(self):
        t = ErrorMessageTranslator(target_lang=Language.EN)
        msg = "list index out of range"
        assert t.translate(msg) == msg

    def test_custom_translation(self):
        self.t.add_translation("custom error", "カスタムエラー")
        assert self.t.translate("custom error") == "カスタムエラー"


# ── Core ErrorTranslator tests ────────────────────────────────────────────────

class TestErrorTranslator:
    def test_analyze_no_ai(self):
        et = ErrorTranslator(target_lang="ja", enable_ai=False)
        result = et.analyze("NameError: name 'bar' is not defined")
        assert isinstance(result, ErrorAnalysis)
        assert result.error_type == "NameError"
        assert result.ai_advice is None
        assert result.translated_message is not None
        assert "bar" in result.translated_message

    def test_translate_only(self):
        et = ErrorTranslator(target_lang="ja", enable_ai=False)
        out = et.translate_only("IndexError: list index out of range")
        assert "インデックス" in out or "範囲" in out

    def test_to_dict(self):
        et = ErrorTranslator(target_lang="ja", enable_ai=False)
        result = et.analyze("TypeError: unsupported operand type")
        d = result.to_dict()
        assert "error_language" in d
        assert "translated_message" in d

    def test_str_representation(self):
        et = ErrorTranslator(target_lang="ja", enable_ai=False)
        result = et.analyze("ZeroDivisionError: division by zero")
        s = str(result)
        assert "ZeroDivisionError" in s
