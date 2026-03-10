#!/usr/bin/env python3
"""Score yesterday's English reading comprehension answers using Google Gen AI SDK.

Writes to GITHUB_OUTPUT:
  yesterday  - date string of the workbook that was scored (YYYYMMDD)
  today      - today's date string (YYYYMMDD)
  level      - determined level (入門 / 初級 / 中級 / 上級 / 熟達)
  scoring_md - path to the scoring result Markdown file
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google import genai  # type: ignore[import]
from google.genai import types  # type: ignore[import]

from prompts import SCORE_SYSTEM_PROMPT

JST = timezone(timedelta(hours=9))
WORKBOOKS_DIR = Path("workbooks")
DEFAULT_MODEL = "gemini-2.0-flash-001"


def build_client() -> tuple[genai.Client, str]:
    """Build a Google Gen AI client backed by Vertex AI."""
    project = (
        os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("CLOUDSDK_CORE_PROJECT")
        or os.environ.get("GCLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT")
    )
    if not project:
        print(
            "Error: No GCP project found. Set GOOGLE_CLOUD_PROJECT, CLOUDSDK_CORE_PROJECT, GCLOUD_PROJECT, or GCP_PROJECT.",
            file=sys.stderr,
        )
        sys.exit(1)
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    return genai.Client(vertexai=True, project=project, location=location), model


def complete(client: genai.Client, model: str, system: str, user: str) -> str:
    """Send a prompt and return the text response."""
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
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y%m%d")
    yesterday_display = yesterday.strftime("%Y年%m月%d日")

    workbook_path = WORKBOOKS_DIR / f"{yesterday_str}.md"
    level = "入門"
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
            if line.startswith("LEVEL:"):
                level = line.replace("LEVEL:", "").strip()
                break

        WORKBOOKS_DIR.mkdir(exist_ok=True)
        scoring_path = WORKBOOKS_DIR / f"{yesterday_str}_scoring.md"
        scoring_path.write_text(
            f"# {yesterday_display} 採点結果\n\n{result.rstrip()}\n",
            encoding="utf-8",
        )
        scoring_md = str(scoring_path)
        print(f"Saved scoring to {scoring_path}")
    else:
        print(f"No workbook found for {yesterday_str}. Using default level: {level}")

    write_github_output("yesterday", yesterday_str)
    write_github_output("today", today_str)
    write_github_output("level", level)
    write_github_output("scoring_md", scoring_md)


if __name__ == "__main__":
    main()
