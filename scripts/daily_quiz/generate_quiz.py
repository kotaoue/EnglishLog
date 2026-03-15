#!/usr/bin/env python3
"""Generate today's English reading comprehension quiz using Google Gen AI SDK.

Reads from environment:
  QUIZ_LEVEL              - level from the score_answers step (入門 / 初級 / 中級 / 上級 / 熟達)
  QUIZ_TODAY              - today's date string (YYYYMMDD)
  GOOGLE_CLOUD_PROJECT    - GCP project ID
  GOOGLE_CLOUD_LOCATION   - GCP region (default: us-central1)
  GEMINI_MODEL            - model name (default: gemini-2.5-flash)

Writes to GITHUB_OUTPUT:
  today  - today's date string (YYYYMMDD)
  level  - level used for quiz generation
"""

import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google import genai  # type: ignore[import]
from google.genai import types  # type: ignore[import]
from google.genai.errors import ClientError  # type: ignore[import]

from prompts import LEVEL_DESCRIPTIONS, QUIZ_SYSTEM_PROMPT

JST = timezone(timedelta(hours=9))
WORKBOOKS_DIR = Path("workbooks")

def build_client() -> tuple[genai.Client, str]:
    """Build a Google Gen AI client backed by Vertex AI."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    if not project:
        print("Error: GOOGLE_CLOUD_PROJECT is not set", file=sys.stderr)
        print("Please set GOOGLE_CLOUD_PROJECT environment variable to your GCP project ID", file=sys.stderr)
        sys.exit(1)

    location = (os.environ.get("GOOGLE_CLOUD_LOCATION") or "").strip() or "us-central1"
    model = (os.environ.get("GEMINI_MODEL") or "").strip() or "gemini-2.5-flash"

    print(f"[Config] Vertex AI Settings:")
    print(f"  - Project ID: {project}")
    print(f"  - Location: {location}")
    print(f"  - Model: {model}")
    print(f"[Info] Creating Vertex AI client...")

    try:
        client = genai.Client(vertexai=True, project=project, location=location)
        print(f"[Success] Vertex AI client created successfully")
        return client, model
    except Exception as e:
        print(f"[Error] Failed to create Vertex AI client: {e}", file=sys.stderr)
        print(f"[Debug] Traceback:\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)


def complete(client: genai.Client, model: str, system: str, user: str) -> str:
    """Send a prompt and return the text response."""
    print(f"[Info] Calling Gemini API with model: {model}")
    print(f"[Debug] User prompt length: {len(user)} chars, System prompt length: {len(system)} chars")

    try:
        response = client.models.generate_content(
            model=model,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        print(f"[Success] Received response from Gemini API")

        text = response.text
        if not text:
            print("[Error] Gemini returned an empty response", file=sys.stderr)
            print(f"[Debug] Response object: {response}", file=sys.stderr)
            sys.exit(1)

        print(f"[Info] Generated text length: {len(text)} chars")
        return text

    except ClientError as e:
        print(f"[Error] Gemini API ClientError: {e}", file=sys.stderr)
        print(f"[Debug] Error details:", file=sys.stderr)
        print(f"  - Status code: {e.status_code if hasattr(e, 'status_code') else 'N/A'}", file=sys.stderr)
        print(f"  - Error message: {e}", file=sys.stderr)

        if "404" in str(e) or "NOT_FOUND" in str(e):
            print(f"\n[Hint] Model '{model}' not found. This could mean:", file=sys.stderr)
            print(f"  1. The model name is incorrect or not available in your region", file=sys.stderr)
            print(f"  2. Your project doesn't have access to this model", file=sys.stderr)
            print(f"  3. You need to use a versioned model ID (e.g., gemini-2.5-flash)", file=sys.stderr)
            print(f"\n  Try setting GEMINI_MODEL environment variable to one of:", file=sys.stderr)
            print(f"    - gemini-2.5-flash", file=sys.stderr)
            print(f"    - gemini-2.5-pro", file=sys.stderr)
            print(f"    - gemini-2.0-flash-001", file=sys.stderr)
            print(f"\n  Example:", file=sys.stderr)
            print(f"    export GEMINI_MODEL=gemini-2.5-flash", file=sys.stderr)

        print(f"\n[Debug] Full traceback:\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"[Error] Unexpected error during API call: {e}", file=sys.stderr)
        print(f"[Debug] Full traceback:\n{traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)


def write_github_output(key: str, value: str) -> None:
    """Write a key-value pair to GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main() -> None:
    client, model = build_client()
    level = os.environ.get("QUIZ_LEVEL", "入門")
    today_str = os.environ.get("QUIZ_TODAY") or datetime.now(JST).strftime("%Y%m%d")
    today_display = datetime.strptime(today_str, "%Y%m%d").strftime("%Y年%m月%d日")

    level_desc = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["入門"])
    print(f"Generating quiz for {today_str} at level: {level} ...")
    quiz = complete(
        client,
        model,
        system=QUIZ_SYSTEM_PROMPT.format(level_desc=level_desc),
        user=f"学習者のレベルは{level}です。今日の英語問題を作成してください。",
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
