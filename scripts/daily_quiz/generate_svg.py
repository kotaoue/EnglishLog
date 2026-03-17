#!/usr/bin/env python3
"""Generate an SVG image showing yesterday's English quiz scoring result.

Reads from environment variables:
  SCORING_DATE  - date string of the scored workbook (YYYYMMDD)
  SCORING_SCORE - score in X/5 format (e.g. 3/5); empty string when no workbook was scored

Writes:
  workbooks/scoring.svg
"""

import os
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


def main() -> None:
    date_str = os.environ.get("SCORING_DATE", "").strip()
    score = os.environ.get("SCORING_SCORE", "").strip()

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
