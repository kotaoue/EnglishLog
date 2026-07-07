#!/usr/bin/env python3
"""Generate today's English reading comprehension quiz using Google Gen AI SDK.

Reads from environment:
  QUIZ_TODAY              - today's date string (YYYYMMDD)
  GOOGLE_CLOUD_PROJECT    - GCP project ID
  GOOGLE_CLOUD_LOCATION   - GCP region (default: us-central1)
  GEMINI_MODEL            - model name (default: gemini-3.5-flash)

Writes to GITHUB_OUTPUT:
  today  - today's date string (YYYYMMDD)
"""

import os
from datetime import datetime
from pathlib import Path

from gemini import JST, WORKBOOKS_DIR, build_client, complete, write_github_output
from prompts import QUIZ_SYSTEM_PROMPT


def _extract_theme(path: Path) -> str | None:
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("## テーマ:"):
                return line.removeprefix("## テーマ:").strip()
    return None


def _extract_score_and_level(path: Path) -> tuple[str, str] | None:
    """Extract score and level from a scoring markdown file.

    Returns (score, level) tuple or None if not found.
    Score format: "X/7", Level format: "入門" etc.
    """
    try:
        content = path.read_text(encoding="utf-8")
        score = ""
        level = ""
        for line in content.splitlines():
            if line.startswith("SCORE:") and not score:
                score = line.replace("SCORE:", "").strip()
            if line.startswith("LEVEL:") and not level:
                level = line.replace("LEVEL:", "").strip()
            if score and level:
                break
        if score and level:
            return (score, level)
    except Exception:
        pass
    return None


def _build_recent_levels_and_scores_prompt(limit: int = 5) -> str:
    """Build a prompt section with recent levels and scores.

    Returns a markdown section describing recent performance.
    """
    scoring_dir = WORKBOOKS_DIR / "scoring"
    if not scoring_dir.exists():
        return ""

    dated_scores = sorted(
        (
            path
            for path in scoring_dir.glob("*_scoring.md")
            if len(path.stem.rsplit("_", 1)[0]) == 8
            and path.stem.rsplit("_", 1)[0].isdigit()
        ),
        reverse=True,
    )

    recent_records: list[tuple[str, str, str]] = []  # (date, level, score)
    for path in dated_scores:
        result = _extract_score_and_level(path)
        if result:
            score, level = result
            date_str = path.stem.rsplit("_", 1)[0]
            recent_records.append((date_str, level, score))
        if len(recent_records) >= limit:
            break

    if not recent_records:
        return ""

    # Build the recent performance section
    records_text = "\n".join(
        f"- {date}: レベル {level}, 正答率 {score}"
        for date, level, score in recent_records
    )
    return (
        "\n\n【最近の学習成績】\n"
        f"{records_text}\n"
        "上記の結果を踏まえて、適切なレベルの問題を出題してください。"
    )


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
    today_str = os.environ.get("QUIZ_TODAY") or datetime.now(JST).strftime("%Y%m%d")
    today_display = datetime.strptime(today_str, "%Y%m%d").strftime("%Y年%m月%d日")

    recent_themes_prompt = _build_recent_themes_prompt()
    recent_levels_and_scores_prompt = _build_recent_levels_and_scores_prompt()
    print(f"Generating quiz for {today_str} ...")
    quiz = complete(
        client,
        model,
        system=QUIZ_SYSTEM_PROMPT,
        user=(
            f"{recent_levels_and_scores_prompt}"
            f"上記の学習成績を踏まえて、最適なレベルで英語問題を作成してください。"
            f"{recent_themes_prompt}"
        ),
    )

    WORKBOOKS_DIR.mkdir(exist_ok=True)
    output_path = WORKBOOKS_DIR / f"{today_str}.md"
    output_path.write_text(
        f"# {today_display} 英語練習帳\n\n---\n\n## 本日の問題\n\n{quiz.strip()}\n",
        encoding="utf-8",
    )
    print(f"Created: {output_path}")

    write_github_output("today", today_str)


if __name__ == "__main__":
    main()
