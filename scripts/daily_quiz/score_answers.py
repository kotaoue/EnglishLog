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
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google import genai  # type: ignore[import]
from google.genai import types  # type: ignore[import]
from google.genai.errors import ClientError  # type: ignore[import]

from prompts import SCORE_SYSTEM_PROMPT

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
            print(f"  3. You need to use a versioned model ID (e.g., gemini-1.5-flash-002)", file=sys.stderr)
            print(f"\n  Try setting GEMINI_MODEL environment variable to one of:", file=sys.stderr)
            print(f"    - gemini-1.5-flash-002", file=sys.stderr)
            print(f"    - gemini-1.5-pro-002", file=sys.stderr)
            print(f"    - gemini-2.0-flash-exp", file=sys.stderr)
            print(f"\n  Example:", file=sys.stderr)
            print(f"    export GEMINI_MODEL=gemini-1.5-flash-002", file=sys.stderr)

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
