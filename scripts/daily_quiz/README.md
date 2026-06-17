
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

Google Cloudの認証を設定します。

> **注意:** ここで指定する `api-project.json` は「サービスアカウント」用の認証情報です。OAuthクライアントIDのJSONでは動作しません。

#### サービスアカウントキー（JSON）の取得手順

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 左メニュー「IAMと管理」→「サービスアカウント」
3. プロジェクト内で新しいサービスアカウントを作成（または既存のものを選択）
4. 「鍵」タブ → 「キーを追加」→「新しいキーを作成」→「JSON」を選択しダウンロード
5. ダウンロードしたJSONファイルを `scripts/daily_quiz/` ディレクトリに `api-project.json` という名前で配置

このJSONファイルを `GOOGLE_APPLICATION_CREDENTIALS` に指定してください。

```sh
export GOOGLE_APPLICATION_CREDENTIALS=./api-project.json
```

### 4. 環境変数の設定

必要な環境変数を設定します。

```sh
# 必須: GCPプロジェクトID
export GOOGLE_CLOUD_PROJECT=$(jq -r '.project_id' ./api-project.json)
echo $GOOGLE_CLOUD_PROJECT

# オプション
export GOOGLE_CLOUD_LOCATION=us-central1
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
