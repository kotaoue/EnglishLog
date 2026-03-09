#!/usr/bin/env python3
"""Generate daily English quiz using a configurable AI provider."""

import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
WORKBOOKS_DIR = Path("workbooks")

SCORE_SYSTEM_PROMPT = """\
あなたは英語の先生です。英語練習帳の回答を採点してください。
各問題について：
1. 回答が正しいか確認
2. 間違いがある場合は正解と解説を提供
3. 全体のスコア（何問中何問正解）を最後に記載

レベル判定もしてください：
- 初級 (Beginner): 基本的な文法ミスが多い
- 中級 (Intermediate): ある程度正しいが細かいミスがある
- 上級 (Advanced): ほぼ正確な英語が書ける

返答の最後に必ず以下の形式でレベルを記載してください：
LEVEL: [初級/中級/上級]\
"""

QUIZ_SYSTEM_PROMPT = """\
あなたは英語の先生です。{level_desc}英語練習問題を作成してください。
問題は以下のMarkdown形式で出力してください：

## テーマ: [テーマ名]

1. [日本語文]
   - あなたの回答: 

2. [日本語文]
   - あなたの回答: 

3. [日本語文]
   - あなたの回答: 

4. [日本語文]
   - あなたの回答: 

5. [日本語文]
   - あなたの回答: 

問題は実用的で、IT・ビジネス・日常会話に関連するものを混ぜてください。\
"""

LEVEL_DESCRIPTIONS = {
    "初級": "現在形・過去形・未来形など基本的な文法に焦点を当てた",
    "中級": "助動詞・進行形・完了形など中程度の文法に焦点を当てた",
    "上級": "仮定法・受動態・複雑な文構造など高度な文法に焦点を当てた",
}


class AIClient(ABC):
    """Abstract base class for AI provider clients."""

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Send a system+user prompt and return the text response."""


class GeminiClient(AIClient):
    """Google Gemini via Google AI Studio (google-generativeai)."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        import google.generativeai as genai  # type: ignore[import]

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model

    def complete(self, system: str, user: str) -> str:
        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system,
        )
        response = model.generate_content(user)
        return response.text


class VertexAIClient(AIClient):
    """Google Gemini via Vertex AI (google-cloud-aiplatform)."""

    def __init__(
        self,
        project: str,
        location: str = "us-central1",
        model: str = "gemini-2.0-flash-001",
    ) -> None:
        import vertexai  # type: ignore[import]
        from vertexai.generative_models import GenerativeModel  # type: ignore[import]

        vertexai.init(project=project, location=location)
        self._GenerativeModel = GenerativeModel
        self._model_name = model

    def complete(self, system: str, user: str) -> str:
        model = self._GenerativeModel(
            model_name=self._model_name,
            system_instruction=system,
        )
        response = model.generate_content(user)
        return response.text


class OpenAIClient(AIClient):
    """OpenAI ChatCompletion (openai)."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        from openai import OpenAI  # type: ignore[import]

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            print("Error: OpenAI returned an empty response", file=sys.stderr)
            sys.exit(1)
        return content


class AnthropicClient(AIClient):
    """Anthropic Claude (anthropic)."""

    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest") -> None:
        import anthropic  # type: ignore[import]

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if not message.content or not hasattr(message.content[0], "text"):
            print("Error: Anthropic returned an empty or unexpected response", file=sys.stderr)
            sys.exit(1)
        return message.content[0].text


def build_client() -> AIClient:
    """Instantiate the AI client selected by the QUIZ_PROVIDER env variable."""
    provider = os.environ.get("QUIZ_PROVIDER", "gemini").lower()

    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY is not set", file=sys.stderr)
            sys.exit(1)
        return GeminiClient(
            api_key=api_key,
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        )

    if provider == "vertexai":
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            print("Error: GOOGLE_CLOUD_PROJECT is not set", file=sys.stderr)
            sys.exit(1)
        return VertexAIClient(
            project=project,
            location=os.environ.get("VERTEX_AI_LOCATION", "us-central1"),
            model=os.environ.get("VERTEX_AI_MODEL", "gemini-2.0-flash-001"),
        )

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY is not set", file=sys.stderr)
            sys.exit(1)
        return OpenAIClient(
            api_key=api_key,
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        )

    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY is not set", file=sys.stderr)
            sys.exit(1)
        return AnthropicClient(
            api_key=api_key,
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
        )

    print(
        f"Error: Unknown QUIZ_PROVIDER '{provider}'. "
        "Choose from: gemini, vertexai, openai, anthropic",
        file=sys.stderr,
    )
    sys.exit(1)


def get_yesterday_workbook(today: datetime) -> str | None:
    """Read yesterday's workbook content if it exists."""
    yesterday = today - timedelta(days=1)
    workbook_path = WORKBOOKS_DIR / f"{yesterday.strftime('%Y%m%d')}.md"
    if workbook_path.exists():
        return workbook_path.read_text(encoding="utf-8")
    return None


def score_yesterday_answers(client: AIClient, content: str) -> tuple[str, str]:
    """Score yesterday's answers and return (feedback, level)."""
    result = client.complete(
        system=SCORE_SYSTEM_PROMPT,
        user=f"以下の英語練習帳の回答を採点してください：\n\n{content}",
    )
    level = "初級"
    for line in result.splitlines():
        if line.startswith("LEVEL:"):
            level = line.replace("LEVEL:", "").strip()
            break
    return result, level


def generate_today_quiz(client: AIClient, level: str) -> str:
    """Generate today's quiz based on the learner's level."""
    level_desc = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["初級"])
    return client.complete(
        system=QUIZ_SYSTEM_PROMPT.format(level_desc=level_desc),
        user=f"学習者のレベルは{level}です。今日の問題を作成してください。",
    )


def write_github_output(key: str, value: str) -> None:
    """Write a key-value pair to GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main() -> None:
    client = build_client()
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
        scoring_result, level = score_yesterday_answers(client, yesterday_content)
        scoring_section = (
            f"\n---\n\n## 前日（{yesterday_display}）の採点結果\n\n{scoring_result.rstrip()}"
        )
    else:
        print("No yesterday's workbook found. Starting at beginner level.")

    print(f"Generating today's quiz at level: {level}...")
    today_quiz = generate_today_quiz(client, level)

    WORKBOOKS_DIR.mkdir(exist_ok=True)
    output_path = WORKBOOKS_DIR / f"{today_str}.md"
    output_path.write_text(
        f"# {today_display} 英語練習帳\n\n"
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
