# error-translator

**エラーを検知 → クリーン化 → 翻訳 → AI アドバイス** を一括で行う Python パッケージ。

Python / JavaScript / TypeScript / Java / 汎用テキストに対応。

---

## インストール

```bash
# 基本（翻訳のみ）
pip install error-translator

# Anthropic Claude でAIアドバイスを使う場合
pip install "error-translator[anthropic]"

# OpenAI GPT でAIアドバイスを使う場合
pip install "error-translator[openai]"

# 両方
pip install "error-translator[all]"
```

---

## クイックスタート

```python
from error_translator import ErrorTranslator

# 日本語に翻訳 + AIアドバイス（環境変数から自動検出）
et = ErrorTranslator(target_lang="ja")

result = et.analyze("""
Traceback (most recent call last):
  File "main.py", line 3, in <module>
    print(items[10])
IndexError: list index out of range
""")

print(result)
```

**出力例:**
```
────────────────────────────────────────────────────────────
  Language : python
  Type     : IndexError
  Original : list index out of range
  翻訳     : リストのインデックスが範囲外です
────────────────────────────────────────────────────────────
  AI Advice
────────────────────────────────────────────────────────────
  1. このエラーの意味：リストの存在しないインデックスにアクセスしようとしています。
  2. 原因：items に10個以上の要素がない可能性があります。
  3. 修正方法：
     - len(items) でリストの長さを確認してください。
     - アクセス前に if len(items) > 10: で確認するか、
       try/except IndexError で捕捉してください。
────────────────────────────────────────────────────────────
```

---

## AIプロバイダーの設定

環境変数を設定するだけで自動検出されます：

```bash
# Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# または OpenAI
export OPENAI_API_KEY="sk-..."
```

明示的に指定する場合：

```python
et = ErrorTranslator(
    target_lang="ja",
    ai_provider="anthropic",   # "anthropic" or "openai"
    ai_api_key="sk-ant-...",
    ai_model="claude-opus-4-6",  # optional
)
```

---

## 対応言語

| プログラミング言語 | 検出方法 |
|---|---|
| Python | Traceback / Exception クラス名 |
| JavaScript / TypeScript | `at` スタックトレース / Error クラス |
| Java | パッケージ付き例外名 |
| 汎用テキスト | フォールバック |

翻訳方向：**英語 → 設定した言語**（デフォルト: 日本語）

---

## CLI

```bash
# 直接入力
error-translator "TypeError: Cannot read properties of undefined"

# パイプ
python -m pytest 2>&1 | error-translator --lang ja

# AIなし（翻訳のみ）
error-translator --no-ai "IndexError: list index out of range"

# プロバイダー指定
error-translator --provider openai "NameError: name 'x' is not defined"
```

---

## APIリファレンス

### `ErrorTranslator`

```python
ErrorTranslator(
    target_lang="ja",        # 翻訳先言語 ("ja" | "en")
    ai_provider=None,        # "anthropic" | "openai" | None(自動)
    ai_api_key=None,         # APIキー（省略時は環境変数）
    ai_model=None,           # モデル名（省略時はデフォルト）
    enable_ai=True,          # False にするとAI無効
)
```

| メソッド | 説明 |
|---|---|
| `.analyze(raw_error)` | フル解析（検出・翻訳・AIアドバイス） |
| `.translate_only(raw_error)` | 翻訳のみ（AI呼び出しなし） |
| `.add_translation(pattern, translation)` | カスタム翻訳を追加 |

### `ErrorAnalysis`（戻り値）

| フィールド | 型 | 説明 |
|---|---|---|
| `raw_error` | str | 元のエラーテキスト |
| `clean_error` | str | ANSI除去・クリーン後 |
| `error_language` | ErrorLanguage | 検出されたプログラミング言語 |
| `error_type` | str \| None | エラークラス名 |
| `error_message` | str | コアエラーメッセージ |
| `translated_message` | str \| None | 翻訳後メッセージ |
| `ai_advice` | str \| None | AIアドバイス |

---

## カスタム翻訳の追加

```python
et = ErrorTranslator(target_lang="ja", enable_ai=False)
et.add_translation("database connection failed", "データベース接続に失敗しました")

result = et.analyze("DatabaseError: database connection failed")
print(result.translated_message)
# → データベース接続に失敗しました
```

---

## 開発

```bash
git clone https://github.com/yourusername/error-translator
cd error-translator
pip install -e ".[dev]"
pytest tests/
```

---

## ライセンス

MIT
