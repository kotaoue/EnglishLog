#!/usr/bin/env python3
"""Generate daily English quiz using OpenAI API."""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openai import OpenAI

JST = timezone(timedelta(hours=9))
WORKBOOKS_DIR = Path("workbooks")

SCORE_SYSTEM_PROMPT = """\
あなたは英語の先生です。英語練習帳の回答を採点してください。
各問題について：
1. 回答が正しいか確認
2. 間違いがある場合は正解と解説を提供
3. 全体のスコア（何問中何問正解）を最後に記載

レベル判定もしてください：
- 初級 (Beginner): 基本的な文法ミスが多い
- 中級 (Intermediate): ある程度正しいが細かいミスがある
- 上級 (Advanced): ほぼ正確な英語が書ける

返答の最後に必ず以下の形式でレベルを記載してください：
LEVEL: [初級/中級/上級]\
"""

QUIZ_SYSTEM_PROMPT = """\
あなたは英語の先生です。{level_desc}英語練習問題を作成してください。
問題は以下のMarkdown形式で出力してください：

## テーマ: [テーマ名]

1. [日本語文]
   - あなたの回答: 

2. [日本語文]
   - あなたの回答: 

3. [日本語文]
   - あなたの回答: 

4. [日本語文]
   - あなたの回答: 

5. [日本語文]
   - あなたの回答: 

問題は実用的で、IT・ビジネス・日常会話に関連するものを混ぜてください。\
"""

LEVEL_DESCRIPTIONS = {
    "初級": "現在形・過去形・未来形など基本的な文法に焦点を当てた",
    "中級": "助動詞・進行形・完了形など中程度の文法に焦点を当てた",
    "上級": "仮定法・受動態・複雑な文構造など高度な文法に焦点を当てた",
}


def get_yesterday_workbook(today: datetime) -> str | None:
    """Read yesterday's workbook content if it exists."""
    yesterday = today - timedelta(days=1)
    workbook_path = WORKBOOKS_DIR / f"{yesterday.strftime('%Y%m%d')}.md"
    if workbook_path.exists():
        return workbook_path.read_text(encoding="utf-8")
    return None


def score_yesterday_answers(client: OpenAI, content: str) -> tuple[str, str]:
    """Score yesterday's answers and return (feedback, level)."""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SCORE_SYSTEM_PROMPT},
            {"role": "user", "content": f"以下の英語練習帳の回答を採点してください：\n\n{content}"},
        ],
    )
    result = response.choices[0].message.content
    level = "初級"
    for line in result.splitlines():
        if line.startswith("LEVEL:"):
            level = line.replace("LEVEL:", "").strip()
            break
    return result, level


def generate_today_quiz(client: OpenAI, level: str) -> str:
    """Generate today's quiz based on the learner's level."""
    level_desc = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["初級"])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT.format(level_desc=level_desc)},
            {"role": "user", "content": f"学習者のレベルは{level}です。今日の問題を作成してください。"},
        ],
    )
    return response.choices[0].message.content


def write_github_output(key: str, value: str) -> None:
    """Write a key-value pair to GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    today = datetime.now(JST)
    today_str = today.strftime("%Y%m%d")
    today_display = today.strftime("%Y年%m月%d日")
    yesterday = today - timedelta(days=1)
    yesterday_display = yesterday.strftime("%Y年%m月%d日")

    yesterday_content = get_yesterday_workbook(today)
    scoring_section = ""
    level = "初級"

    if yesterday_content:
        print("Scoring yesterday's answers...")
        scoring_result, level = score_yesterday_answers(client, yesterday_content)
        scoring_section = (
            f"\n---\n\n## 前日（{yesterday_display}）の採点結果\n\n{scoring_result.rstrip()}"
        )
    else:
        print("No yesterday's workbook found. Starting at beginner level.")

    print(f"Generating today's quiz at level: {level}...")
    today_quiz = generate_today_quiz(client, level)

    WORKBOOKS_DIR.mkdir(exist_ok=True)
    output_path = WORKBOOKS_DIR / f"{today_str}.md"
    output_path.write_text(
        f"# {today_display} 英語練習帳\n\n"
        f"## レベル: {level}\n"
        f"{scoring_section}\n\n"
        f"---\n\n"
        f"## 本日の問題\n\n"
        f"{today_quiz}\n",
        encoding="utf-8",
    )
    print(f"Created: {output_path}")

    write_github_output("today", today_str)
    write_github_output("level", level)


if __name__ == "__main__":
    main()
