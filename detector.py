"""Detect, clean, and extract structured info from raw error text."""

from __future__ import annotations
import re
from typing import Optional, Tuple
from error_translator.models import ErrorLanguage

# ANSI escape codes
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")

# ── Python patterns ──────────────────────────────────────────────────────────
_PY_ERROR_RE = re.compile(
    r"(?P<type>[A-Za-z]+(?:Error|Exception|Warning|Interrupt|Exit|StopIteration|"
    r"GeneratorExit|SystemExit|KeyboardInterrupt))"
    r"(?:\s*:\s*(?P<msg>.+))?",
    re.MULTILINE,
)
_PY_TRACEBACK = re.compile(r"Traceback \(most recent call last\):")

# ── JavaScript / TypeScript patterns ────────────────────────────────────────
_JS_ERROR_RE = re.compile(
    r"(?P<type>[A-Za-z]+Error)(?:\s*:\s*(?P<msg>.+))?",
    re.MULTILINE,
)
_JS_STACK_LINE = re.compile(r"^\s+at\s+.+$", re.MULTILINE)

# ── Java patterns ────────────────────────────────────────────────────────────
_JAVA_EXCEPTION_RE = re.compile(
    r"(?P<type>(?:[a-z]+\.)+[A-Z][A-Za-z]+(?:Exception|Error|Throwable))"
    r"(?:\s*:\s*(?P<msg>.+))?",
    re.MULTILINE,
)
_JAVA_CAUSED_BY = re.compile(r"^(?:Caused by:|Exception in thread)", re.MULTILINE)
_JAVA_STACK_LINE = re.compile(r"^\s+at\s+[\w\.$]+\(.+\)$", re.MULTILINE)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes."""
    return _ANSI_RE.sub("", text)


def _detect_language(text: str) -> ErrorLanguage:
    if _PY_TRACEBACK.search(text) or _PY_ERROR_RE.search(text):
        # Prefer Python if 'Traceback' present
        if _PY_TRACEBACK.search(text):
            return ErrorLanguage.PYTHON
        if _JAVA_EXCEPTION_RE.search(text):
            return ErrorLanguage.JAVA
        if _JS_STACK_LINE.search(text):
            return ErrorLanguage.JAVASCRIPT
        return ErrorLanguage.PYTHON
    if _JAVA_CAUSED_BY.search(text) or _JAVA_EXCEPTION_RE.search(text):
        return ErrorLanguage.JAVA
    if _JS_STACK_LINE.search(text) or _JS_ERROR_RE.search(text):
        return ErrorLanguage.JAVASCRIPT
    return ErrorLanguage.GENERIC


def _extract_python(text: str) -> Tuple[Optional[str], str]:
    """Return (error_type, core_message) for Python errors."""
    # Strip traceback lines
    lines = text.splitlines()
    core_lines = [
        l for l in lines
        if not l.startswith("  File ") and not l.startswith("    ")
        and not _PY_TRACEBACK.match(l)
    ]
    core = "\n".join(core_lines).strip()
    m = _PY_ERROR_RE.search(core)
    if m:
        return m.group("type"), (m.group("msg") or "").strip() or core
    return None, core or text.strip()


def _extract_javascript(text: str) -> Tuple[Optional[str], str]:
    """Return (error_type, core_message) for JS/TS errors."""
    # Remove stack lines
    clean = _JS_STACK_LINE.sub("", text).strip()
    m = _JS_ERROR_RE.search(clean)
    if m:
        return m.group("type"), (m.group("msg") or "").strip() or clean
    return None, clean or text.strip()


def _extract_java(text: str) -> Tuple[Optional[str], str]:
    """Return (error_type, core_message) for Java errors."""
    clean = _JAVA_STACK_LINE.sub("", text).strip()
    m = _JAVA_EXCEPTION_RE.search(clean)
    if m:
        type_full = m.group("type")
        short_type = type_full.split(".")[-1]
        msg = (m.group("msg") or "").strip()
        return short_type, msg or type_full
    return None, clean or text.strip()


class ErrorDetector:
    """Detect language, clean, and extract structured error info."""

    def detect(self, raw: str) -> dict:
        """
        Analyze raw error text.

        Returns dict with keys:
            clean_error, error_language, error_type, error_message
        """
        cleaned = strip_ansi(raw).strip()
        lang = _detect_language(cleaned)

        if lang == ErrorLanguage.PYTHON:
            error_type, message = _extract_python(cleaned)
        elif lang in (ErrorLanguage.JAVASCRIPT, ErrorLanguage.TYPESCRIPT):
            error_type, message = _extract_javascript(cleaned)
        elif lang == ErrorLanguage.JAVA:
            error_type, message = _extract_java(cleaned)
        else:
            error_type = None
            message = cleaned

        return {
            "clean_error": cleaned,
            "error_language": lang,
            "error_type": error_type,
            "error_message": message,
        }
