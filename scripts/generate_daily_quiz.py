#!/usr/bin/env python3
"""Generate daily English reading comprehension quiz using Google Gen AI SDK."""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google import genai  # type: ignore[import]

from prompts import LEVEL_DESCRIPTIONS, QUIZ_SYSTEM_PROMPT, SCORE_SYSTEM_PROMPT

JST = timezone(timedelta(hours=9))
WORKBOOKS_DIR = Path("workbooks")
DEFAULT_MODEL = "gemini-2.0-flash-001"


def build_client() -> tuple[genai.Client, str]:
    """Build a Google Gen AI client backed by Vertex AI."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        print("Error: GOOGLE_CLOUD_PROJECT is not set", file=sys.stderr)
        sys.exit(1)
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    client = genai.Client(vertexai=True, project=project, location=location)
    return client, model


def complete(client: genai.Client, model: str, system: str, user: str) -> str:
    """Send a prompt and return the text response."""
    from google.genai import types  # type: ignore[import]

    response = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    text = response.text
    if not text:
        print("Error: Gemini returned an empty response", file=sys.stderr)
        sys.exit(1)
    return text


def get_yesterday_workbook(today: datetime) -> str | None:
    """Read yesterday's workbook content if it exists."""
    yesterday = today - timedelta(days=1)
    workbook_path = WORKBOOKS_DIR / f"{yesterday.strftime('%Y%m%d')}.md"
    if workbook_path.exists():
        return workbook_path.read_text(encoding="utf-8")
    return None


def score_yesterday_answers(
    client: genai.Client, model: str, content: str
) -> tuple[str, str]:
    """Score yesterday's answers and return (feedback, level)."""
    result = complete(
        client,
        model,
        system=SCORE_SYSTEM_PROMPT,
        user=f"以下の英語読解練習帳の回答を採点してください：\n\n{content}",
    )
    level = "初級"
    for line in result.splitlines():
        if line.startswith("LEVEL:"):
            level = line.replace("LEVEL:", "").strip()
            break
    return result, level


def generate_today_quiz(client: genai.Client, model: str, level: str) -> str:
    """Generate today's reading comprehension quiz based on the learner's level."""
    level_desc = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["初級"])
    return complete(
        client,
        model,
        system=QUIZ_SYSTEM_PROMPT.format(level_desc=level_desc),
        user=f"学習者のレベルは{level}です。今日の読解問題を作成してください。",
    )


def write_github_output(key: str, value: str) -> None:
    """Write a key-value pair to GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main() -> None:
    client, model = build_client()
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
        scoring_result, level = score_yesterday_answers(client, model, yesterday_content)
        scoring_section = (
            f"\n---\n\n## 前日（{yesterday_display}）の採点結果\n\n{scoring_result.rstrip()}"
        )
    else:
        print("No yesterday's workbook found. Starting at beginner level.")

    print(f"Generating today's quiz at level: {level}...")
    today_quiz = generate_today_quiz(client, model, level)

    WORKBOOKS_DIR.mkdir(exist_ok=True)
    output_path = WORKBOOKS_DIR / f"{today_str}.md"
    output_path.write_text(
        f"# {today_display} 英語読解練習帳\n\n"
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
