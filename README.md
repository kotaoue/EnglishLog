# EnglishLog
Log of studying English.

# Histories
* [2022](2022/)

# 毎日英語練習帳（Daily Quiz）

毎日 0:00 JST に GitHub Actions が自動で英語練習問題を生成し、PR として作成します。

## AI プロバイダーの選択

`QUIZ_PROVIDER` リポジトリ変数（`Settings → Variables → Actions`）で使用する AI を切り替えられます。

| `QUIZ_PROVIDER` 値 | サービス | 無料枠 | 推奨度 | 必要な Secret / Variable |
|---|---|---|---|---|
| `gemini` **(デフォルト)** | Google Gemini API (AI Studio) | ✅ あり (Gemini 2.0 Flash: 15 RPM 無料) | ⭐⭐⭐ | `GEMINI_API_KEY` |
| `vertexai` | Google Cloud Vertex AI | ⚠️ GCP 無料枠内 | ⭐⭐⭐ | `GOOGLE_CREDENTIALS_JSON`, `GOOGLE_CLOUD_PROJECT` |
| `openai` | OpenAI GPT-4o | ❌ 従量課金のみ | ⭐⭐ | `OPENAI_API_KEY` |
| `anthropic` | Anthropic Claude | ❌ 従量課金のみ | ⭐⭐ | `ANTHROPIC_API_KEY` |

> **コスト感（1日あたり）**: Gemini 無料枠 → $0 / Vertex AI ~$0.001 / OpenAI GPT-4o ~$0.01 / Claude Haiku ~$0.005

---

## セットアップ手順

### 共通: プロバイダーの指定

`Settings → Secrets and variables → Actions → Variables` で変数を追加します。

| Name | Value（例） |
|---|---|
| `QUIZ_PROVIDER` | `gemini` |

指定しない場合は `gemini` が使われます。

---

### Option A: Google Gemini API (AI Studio) ★おすすめ・無料枠あり

1. [Google AI Studio](https://aistudio.google.com/) にアクセスしてログイン
2. **「Get API key」→「Create API key」** をクリック
3. 発行されたキー（`AIza...`）をコピー
4. リポジトリの **Settings → Secrets → Actions → New repository secret** で登録:
   - Name: `GEMINI_API_KEY`
5. Variables で `QUIZ_PROVIDER` = `gemini` を設定（またはデフォルトのまま）

> 無料枠: Gemini 2.0 Flash は **1分あたり 15リクエスト、1日1,500リクエスト** まで無料。このワークフローは通常1日2リクエスト（採点＋問題生成）のみ。

---

### Option B: Google Cloud Vertex AI

Vertex AI は Google Cloud プロジェクト上で Gemini を呼び出す企業向けオプションです。

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成し、**Vertex AI API** を有効化
2. **IAM → サービスアカウント** を作成し、`Vertex AI User` ロールを付与
3. サービスアカウントの **JSON キーを作成**してダウンロード
4. リポジトリの Secrets に登録:
   - `GOOGLE_CREDENTIALS_JSON`: ダウンロードした JSON の内容（全文）
5. Variables に登録:
   - `QUIZ_PROVIDER`: `vertexai`
   - `GOOGLE_CLOUD_PROJECT`: GCP プロジェクト ID（例: `my-project-123`）
   - `VERTEX_AI_LOCATION`: `us-central1`（任意、デフォルト値）

---

### Option C: OpenAI

1. [platform.openai.com](https://platform.openai.com/) でアカウント登録・ログイン
2. **[API keys](https://platform.openai.com/api-keys) → 「+ Create new secret key」** をクリック
3. 発行されたキー（`sk-...`）をコピーし Secrets に登録:
   - `OPENAI_API_KEY`
4. Variables で `QUIZ_PROVIDER` = `openai` を設定

> ⚠️ [Usage limits](https://platform.openai.com/settings/organization/limits) で月次の利用上限を設定することを推奨します。

---

### Option D: Anthropic Claude

1. [console.anthropic.com](https://console.anthropic.com/) でアカウント登録・ログイン
2. **API Keys → 「Create Key」** でキーを発行（`sk-ant-...`）
3. Secrets に登録:
   - `ANTHROPIC_API_KEY`
4. Variables で `QUIZ_PROVIDER` = `anthropic` を設定

---

## 手動実行

Actions タブ → **Daily English Quiz** → **Run workflow** で手動実行できます。
実行時に `provider` フィールドを入力すると、`QUIZ_PROVIDER` 変数より優先して使われます。