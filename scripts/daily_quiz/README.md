
# daily_quiz ディレクトリについて

このディレクトリは、英語リーディング練習のための「日替わりクイズ」自動生成・採点スクリプト群です。

## 各ファイルの概要

- `generate_quiz.py` : 日替わり英語クイズ生成スクリプト
- `score_answers.py` : 回答の自動採点・レベル判定スクリプト
- `prompts.py` : AIプロンプト定義
- `Pipfile` : 必要なPythonパッケージ管理

## ローカルでの実行手順

### 1. 前提条件

- Python 3.12以上
- pipenvがインストールされていること
- Google Cloud PlatformのプロジェクトとVertex AI APIが有効になっていること

### 2. 依存パッケージのインストール

```sh
cd scripts/daily_quiz/
pipenv install
```

### 3. 認証情報の設定

Google Cloudの認証を設定します。以下のいずれかの方法を選択してください。

#### 方法A: サービスアカウントキーを使用

```sh
export GOOGLE_APPLICATION_CREDENTIALS=./client_secret.json
```

#### 方法B: gcloud CLIで認証

```sh
gcloud auth application-default login
```

### 4. 環境変数の設定

必要な環境変数を設定します。

```sh
# 必須: GCPプロジェクトID
export GOOGLE_CLOUD_PROJECT=$(jq -r '.installed.project_id' ./client_secret.json)
echo $GOOGLE_CLOUD_PROJECT

# オプション
export GOOGLE_CLOUD_LOCATION=us-central1
export GEMINI_MODEL=gemini-1.5-flash-002
export QUIZ_TODAY=20260315
export QUIZ_LEVEL=入門

export PYTHONPATH=scripts/daily_quiz
```

### 5. スクリプトの実行

```sh
# クイズ生成
pipenv run python generate_quiz.py

# 採点
pipenv run python score_answers.py
```

### トラブルシューティング

#### モデルが見つからないエラー (404 NOT_FOUND)

```text
Publisher Model `projects/.../models/gemini-1.5-flash` was not found
```

このエラーが出た場合、以下を確認してください:

1. **バージョン付きモデルIDを使用**: Vertex AIではバージョン付きモデル名が必要です

   ```sh
   export GEMINI_MODEL=gemini-1.5-flash-002
   ```

   利用可能なモデル:
   - `gemini-1.5-flash-002`
   - `gemini-1.5-pro-002`
   - `gemini-2.0-flash-exp`

2. **リージョンの確認**: モデルが指定したリージョンで利用可能か確認

3. **プロジェクトのアクセス権限**: プロジェクトがVertex AI APIとGeminiモデルへのアクセス権を持っているか確認

#### PYTHONPATHエラー

```text
ModuleNotFoundError: No module named 'prompts'
```

このエラーが出た場合、PYTHONPATHを設定してください:

```sh
export PYTHONPATH=scripts/daily_quiz
```

または、スクリプトを実行するディレクトリを変更してください。

---

ご不明点があれば、プロジェクトルートの `README.md` もご参照ください。
