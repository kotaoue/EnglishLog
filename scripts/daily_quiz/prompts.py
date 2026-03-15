"""AI prompt templates for the daily English quiz workflow."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


SCORE_SYSTEM_PROMPT: str = _load_prompt("score_system_prompt.txt")

QUIZ_SYSTEM_PROMPT: str = _load_prompt("quiz_system_prompt.txt")

LEVEL_DESCRIPTIONS: dict[str, str] = {
    "入門": "中学1〜2年レベルの基本単語のみ使い、1〜2文の短い英文で構成された",
    "初級": "中学3年〜高校1年レベルの、日常的な話題を扱う短いパッセージで構成された",
    "中級": "高校2〜3年レベルのビジネス・日常英語で、やや複雑な文構造を含む",
    "上級": "大学入試〜TOEIC 730点レベルの、専門用語を含むビジネス・技術文書レベルの",
    "熟達": "TOEIC 900点〜TOEFL レベルの学術論文・専門記事を含む複雑な構文の",
}
