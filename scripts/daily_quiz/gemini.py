import os
import sys
import traceback
from datetime import timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from google import genai  # type: ignore[import]
from google.genai import types  # type: ignore[import]
from google.genai.errors import ClientError  # type: ignore[import]

JST = timezone(timedelta(hours=9))
WORKBOOKS_DIR = Path("workbooks")
SCORING_DIR = WORKBOOKS_DIR / "scoring"


def _compact_traceback() -> str:
    return traceback.format_exc().strip().replace("\n", "\\n")


def _list_available_gemini_models(project: str, location: str, limit: int = 12) -> list[str]:
    """List available Gemini model IDs via Vertex AI publisher models API."""
    try:
        import google.auth  # type: ignore[import]
        from google.auth.transport.requests import AuthorizedSession  # type: ignore[import]

        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        session = AuthorizedSession(credentials)
        parent = quote(f"projects/{project}/locations/{location}/publishers/google", safe="/")
        url = f"https://{location}-aiplatform.googleapis.com/v1/{parent}/models"
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            return []

        payload = response.json() if response.content else {}
        models = payload.get("models", [])
        names: list[str] = []
        for item in models:
            full_name = str(item.get("name", ""))
            model_id = full_name.rsplit("/", 1)[-1] if full_name else ""
            if model_id.startswith("gemini-"):
                names.append(model_id)

        # Keep stable order while removing duplicates.
        unique_names = list(dict.fromkeys(names))
        return unique_names[:limit]
    except Exception:
        return []

def build_client() -> tuple[genai.Client, str]:
    """Build a Google Gen AI client backed by Vertex AI."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    if not project:
        print("[Error] GOOGLE_CLOUD_PROJECT is not set (required)", file=sys.stderr)
        sys.exit(1)

    location = (os.environ.get("GOOGLE_CLOUD_LOCATION") or "").strip() or "us-central1"
    model = "gemini-3.5-flash"

    print(f"[Config] VertexAI init project={project} location={location} model={model}")

    try:
        client = genai.Client(vertexai=True, project=project, location=location)
        print("[Success] VertexAI client created")
        return client, model
    except Exception as e:
        print(f"[Error] VertexAI client creation failed: {type(e).__name__}: {e}", file=sys.stderr)
        if os.getenv("QUIZ_DEBUG") == "1":
            print(f"[Debug] traceback={_compact_traceback()}", file=sys.stderr)
        sys.exit(1)


def complete(client: genai.Client, model: str, system: str, user: str) -> str:
    """Send a prompt and return the text response."""
    print(
        f"[Info] Gemini request model={model} user_prompt_chars={len(user)} "
        f"system_prompt_chars={len(system)}"
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=user,
            config=types.GenerateContentConfig(system_instruction=system),
        )
        print(f"[Success] Received response from Gemini API")

        text = response.text
        if not text:
            print(f"[Error] Gemini returned empty response model={model} response={response}", file=sys.stderr)
            sys.exit(1)

        print(f"[Info] Generated text length: {len(text)} chars")
        return text

    except ClientError as e:
        status_code = getattr(e, "status_code", "N/A")
        response_json = getattr(e, "response_json", None)
        hint = ""
        candidate_models: list[str] = []
        if "404" in str(e) or "NOT_FOUND" in str(e):
            hint = " hint=model_unavailable_for_project_or_region"
            project = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
            location = (os.environ.get("GOOGLE_CLOUD_LOCATION") or "").strip() or "us-central1"
            if project:
                candidate_models = _list_available_gemini_models(project, location)

        candidates_text = ""
        if candidate_models:
            candidates_text = f" candidates={','.join(candidate_models)}"

        print(
            f"[Error] Gemini API request failed status={status_code} model={model} "
            f"error={e} response_json={response_json}{hint}{candidates_text}",
            file=sys.stderr,
        )

        if os.getenv("QUIZ_DEBUG") == "1":
            print(f"[Debug] traceback={_compact_traceback()}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"[Error] Unexpected Gemini API error: {type(e).__name__}: {e}", file=sys.stderr)
        if os.getenv("QUIZ_DEBUG") == "1":
            print(f"[Debug] traceback={_compact_traceback()}", file=sys.stderr)
        sys.exit(1)


def write_github_output(key: str, value: str) -> None:
    """Write a key-value pair to GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")
