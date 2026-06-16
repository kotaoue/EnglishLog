#!/usr/bin/env python3
"""Generate today's English reading comprehension quiz using Google Gen AI SDK.

Reads from environment:
  QUIZ_LEVEL              - level from the score_answers step (入門 / 初級 / 初中級 / 準中級 / 中級 / 上級 / 熟達)
  QUIZ_TODAY              - today's date string (YYYYMMDD)
  GOOGLE_CLOUD_PROJECT    - GCP project ID
  GOOGLE_CLOUD_LOCATION   - GCP region (default: us-central1)
  GEMINI_MODEL            - model name (default: gemini-3.5-flash)

Writes to GITHUB_OUTPUT:
  today  - today's date string (YYYYMMDD)
  level  - level used for quiz generation
"""

import os
from datetime import datetime
from pathlib import Path

from gemini import JST, WORKBOOKS_DIR, build_client, complete, write_github_output
from prompts import LEVEL_DESCRIPTIONS, QUIZ_SYSTEM_PROMPT


def _extract_theme(path: Path) -> str | None:
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("## テーマ:"):
                return line.removeprefix("## テーマ:").strip()
    return None


def _build_recent_themes_prompt(limit: int = 10) -> str:
    dated_workbooks = sorted(
        (
            path
            for path in WORKBOOKS_DIR.glob("*.md")
            if len(path.stem) == 8 and path.stem.isdigit()
        ),
        reverse=True,
    )
    recent_themes: list[str] = []
    for path in dated_workbooks:
        theme = _extract_theme(path)
        if theme:
            recent_themes.append(theme)
        if len(recent_themes) >= limit:
            break

    if not recent_themes:
        return ""

    listed = "\n".join(f"- {theme}" for theme in recent_themes)
    return (
        "\n\n最近出題されたテーマは以下のようなものです。\n"
        f"{listed}\n"
        "できるだけ重複しない新しいテーマを選んでください。"
    )


def main() -> None:
    client, model = build_client()
    level = os.environ.get("QUIZ_LEVEL", "入門")
    today_str = os.environ.get("QUIZ_TODAY") or datetime.now(JST).strftime("%Y%m%d")
    today_display = datetime.strptime(today_str, "%Y%m%d").strftime("%Y年%m月%d日")

    level_desc = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["入門"])
    recent_themes_prompt = _build_recent_themes_prompt()
    print(f"Generating quiz for {today_str} at level: {level} ...")
    quiz = complete(
        client,
        model,
        system=QUIZ_SYSTEM_PROMPT.format(level_desc=level_desc),
        user=(
            f"学習者のレベルは{level}です。今日の英語問題を作成してください。"
            f"{recent_themes_prompt}"
        ),
    )

    WORKBOOKS_DIR.mkdir(exist_ok=True)
    output_path = WORKBOOKS_DIR / f"{today_str}.md"
    output_path.write_text(
        f"# {today_display} 英語練習帳\n\n"
        f"## レベル: {level}\n\n"
        f"---\n\n"
        f"## 本日の問題\n\n"
        f"{quiz.strip()}\n",
        encoding="utf-8",
    )
    print(f"Created: {output_path}")

    write_github_output("today", today_str)
    write_github_output("level", level)


if __name__ == "__main__":
    main()
