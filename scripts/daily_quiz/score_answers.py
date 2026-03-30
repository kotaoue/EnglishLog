#!/usr/bin/env python3
"""Score English reading comprehension answers using Google Gen AI SDK.

Reads from environment variables (optional):
  TARGET_DATE - date string of the workbook to score (YYYYMMDD).
                Defaults to yesterday when omitted.

Writes to GITHUB_OUTPUT:
  yesterday  - date string of the workbook that was scored (YYYYMMDD)
  today      - today's date string (YYYYMMDD)
  level      - determined level (入門 / 初級 / 初中級 / 準中級 / 中級 / 上級 / 熟達)
  score      - score in X/5 format (e.g. 3/5)
  scoring_md - path to the scoring result Markdown file
"""

import os
from datetime import datetime, timedelta

from gemini import JST, WORKBOOKS_DIR, build_client, complete, write_github_output
from prompts import SCORE_SYSTEM_PROMPT


def main() -> None:
    client, model = build_client()
    today = datetime.now(JST)
    today_str = today.strftime("%Y%m%d")

    target_date_str = os.environ.get("TARGET_DATE", "").strip()
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, "%Y%m%d").replace(tzinfo=JST)
        except ValueError:
            raise SystemExit(
                f"Invalid TARGET_DATE format: '{target_date_str}'. Expected YYYYMMDD (e.g. 20260101)."
            )
    else:
        target_date = today - timedelta(days=1)
    target_date_str = target_date.strftime("%Y%m%d")
    target_date_display = target_date.strftime("%Y年%m月%d日")

    workbook_path = WORKBOOKS_DIR / f"{target_date_str}.md"
    level = ""
    score = ""
    scoring_md = ""

    if workbook_path.exists():
        content = workbook_path.read_text(encoding="utf-8")
        print(f"Scoring {workbook_path} ...")
        result = complete(
            client,
            model,
            system=SCORE_SYSTEM_PROMPT,
            user=f"以下の英語練習帳の回答を採点してください：\n\n{content}",
        )
        for line in result.splitlines():
            if line.startswith("SCORE:") and not score:
                score = line.replace("SCORE:", "").strip()
            if line.startswith("LEVEL:") and not level:
                level = line.replace("LEVEL:", "").strip()
            if score and level:
                break
        if not level:
            level = "入門"

        WORKBOOKS_DIR.mkdir(exist_ok=True)
        scoring_path = WORKBOOKS_DIR / f"{target_date_str}_scoring.md"
        scoring_path.write_text(
            f"# {target_date_display} 採点結果\n\n{result.rstrip()}\n",
            encoding="utf-8",
        )
        scoring_md = str(scoring_path)
        print(f"Saved scoring to {scoring_path}")
    else:
        level = "入門"
        print(f"No workbook found for {target_date_str}. Using default level: {level}")

    write_github_output("yesterday", target_date_str)
    write_github_output("today", today_str)
    write_github_output("level", level)
    write_github_output("score", score)
    write_github_output("scoring_md", scoring_md)


if __name__ == "__main__":
    main()
