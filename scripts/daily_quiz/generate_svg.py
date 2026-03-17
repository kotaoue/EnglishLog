#!/usr/bin/env python3
"""Generate an SVG image showing yesterday's English quiz scoring result.

Reads from environment variables (optional):
  SCORING_DATE  - date string of the scored workbook (YYYYMMDD)
  SCORING_SCORE - score in X/5 format (e.g. 3/5)

When the environment variables are absent the script auto-detects the date and
score by scanning ``workbooks/`` for the most recent ``*_scoring.md`` file.

Writes:
  workbooks/scoring.svg
"""

import os
import re
from datetime import datetime, timedelta

from gemini import JST, WORKBOOKS_DIR

SVG_PATH = WORKBOOKS_DIR / "scoring.svg"

# Dimensions chosen to sit comfortably alongside a book cover and Spotify album
# art in a GitHub profile README table cell.
SVG_WIDTH = 200
SVG_HEIGHT = 200


def _parse_date(date_str: str) -> datetime:
    """Parse a YYYYMMDD string and return a datetime in JST."""
    return datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=JST)


def generate_svg(date_display: str, score: str) -> str:
    """Return SVG markup for the given display date and score."""
    score_text = score if score else "N/A"
    cx = SVG_WIDTH // 2

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}"'
        f' width="{SVG_WIDTH}" height="{SVG_HEIGHT}">\n'
        f'  <rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" rx="12"'
        f' fill="#ffffff" stroke="#d1d5db" stroke-width="1"/>\n'
        f'  <text x="{cx}" y="55"'
        f' font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"'
        f' font-size="13" fill="#6e7681" text-anchor="middle">英語スコア</text>\n'
        f'  <text x="{cx}" y="110"'
        f' font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"'
        f' font-size="24" fill="#0969da" text-anchor="middle"'
        f' font-weight="600">{date_display}</text>\n'
        f'  <text x="{cx}" y="168"'
        f' font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"'
        f' font-size="52" fill="#1a7f37" text-anchor="middle"'
        f' font-weight="700">{score_text}</text>\n'
        f'</svg>\n'
    )


def _latest_scoring() -> tuple[str, str]:
    """Return (YYYYMMDD, score) from the most recent workbooks/*_scoring.md file.

    Returns empty strings when no scoring file is found.
    """
    pattern = re.compile(r"^(\d{8})_scoring\.md$")
    candidates = []
    for p in WORKBOOKS_DIR.iterdir():
        m = pattern.match(p.name)
        if m:
            candidates.append((m.group(1), p))
    if not candidates:
        return "", ""
    candidates.sort(key=lambda x: x[0], reverse=True)
    date_str, path = candidates[0]
    score = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("SCORE:") and not score:
            score = line.replace("SCORE:", "").strip()
            break
    return date_str, score


def main() -> None:
    date_str = os.environ.get("SCORING_DATE", "").strip()
    score = os.environ.get("SCORING_SCORE", "").strip()

    if not date_str or not score:
        detected_date, detected_score = _latest_scoring()
        if not date_str:
            date_str = detected_date
        if not score:
            score = detected_score

    if date_str:
        yesterday = _parse_date(date_str)
    else:
        yesterday = datetime.now(JST) - timedelta(days=1)

    # e.g. "Mar 16"  (no zero-padding on day)
    date_display = f"{yesterday.strftime('%b')} {yesterday.day}"

    svg_content = generate_svg(date_display, score)

    WORKBOOKS_DIR.mkdir(exist_ok=True)
    SVG_PATH.write_text(svg_content, encoding="utf-8")
    print(f"Saved SVG to {SVG_PATH}")


if __name__ == "__main__":
    main()
