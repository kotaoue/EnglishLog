# EnglishLog
Log of studying English.

# Histories
* [2022](2022/)

# 毎日英語練習帳（Daily Quiz）

毎日 0:00 JST に GitHub Actions が自動で英語練習問題を生成し、PR として作成します。

## セットアップ: OpenAI API キーの発行

### 料金について

OpenAI API は **従量課金制**（無料プランなし）です。
- 新規アカウント作成時に少額の無料クレジット（$5〜$18 程度）が付与される場合があります。
- このワークフローの1日あたりのコストは **$0.01 未満**（約1〜2円）の見込みです。
  - GPT-4o: 入力 $2.50 / 1M トークン、出力 $10.00 / 1M トークン
  - 1回の実行で採点 + 問題生成の 2回 APIを呼び出し、合計 ~2,000〜3,000 トークン程度

最新の料金は [OpenAI Pricing](https://openai.com/api/pricing/) をご確認ください。

### API キーの発行手順

1. [platform.openai.com](https://platform.openai.com/) にアクセスしてアカウント登録（または既存アカウントでログイン）
2. **[API keys](https://platform.openai.com/api-keys)** ページを開く
3. **「+ Create new secret key」** をクリック
4. 名前を入力（例: `EnglishLog`）し **「Create secret key」** をクリック
5. 表示されたキー（`sk-...`）をコピーして安全な場所に保存（再表示不可）

> ⚠️ **使いすぎ防止**: [Usage limits](https://platform.openai.com/settings/organization/limits) で月次の利用上限（例: $1〜$5）を設定することを推奨します。

### GitHub Secrets への登録

1. このリポジトリの **Settings → Secrets and variables → Actions** を開く
2. **「New repository secret」** をクリック
3. Name: `OPENAI_API_KEY`、Secret: コピーした API キーを貼り付けて **「Add secret」**

これで毎日 0:00 JST に自動実行されます。手動実行は Actions タブ → **Daily English Quiz** → **Run workflow** で可能です。