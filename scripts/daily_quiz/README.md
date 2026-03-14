
# daily_quiz ディレクトリについて

このディレクトリは、英語リーディング練習のための「日替わりクイズ」自動生成・採点スクリプト群です。

## 各ファイルの概要

- `generate_quiz.py` : 日替わり英語クイズ生成スクリプト
- `score_answers.py` : 回答の自動採点・レベル判定スクリプト
- `prompts.py` : AIプロンプト定義
- `Pipfile` : 必要なPythonパッケージ管理

## 実行手順

1. 必要なパッケージのインストール

   このディレクトリで以下を実行してください。

   ```sh
   pipenv install
   ```

2. スクリプトの実行

   例: クイズ生成

   ```sh
   pipenv run python generate_quiz.py
   ```

   例: 採点

   ```sh
   pipenv run python score_answers.py
   ```

   必要に応じて環境変数を設定してください（Google Cloud関連など）。

---

ご不明点があれば、プロジェクトルートの `README.md` もご参照ください。
