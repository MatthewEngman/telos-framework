import json
import os
import re
import urllib.error
import urllib.request
from typing import Literal, Optional

from openai import OpenAI

from .schema import TIRSchema

BackendName = Literal["auto", "openai", "ollama", "mock"]


def _env_backend() -> Optional[BackendName]:
    raw = (os.getenv("TELOS_LLM_BACKEND") or "").strip().lower()
    if raw in ("openai", "ollama", "mock", "auto"):
        return raw  # type: ignore[return-value]
    return None


def _ollama_base_url() -> str:
    return (os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")


def _ollama_model() -> str:
    return os.getenv("TELOS_OLLAMA_MODEL") or "llama3.2"


def _http_json(url: str, payload: dict, timeout: float = 120.0) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ollama_get_tags(base_url: str, timeout: float = 2.0) -> Optional[dict]:
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def _ollama_reachable(base_url: str, timeout: float = 2.0) -> bool:
    return _ollama_get_tags(base_url, timeout=timeout) is not None


def _ollama_model_installed(base_url: str, model: str, timeout: float = 2.0) -> bool:
    data = _ollama_get_tags(base_url, timeout=timeout)
    if not data:
        return False
    names = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    root = model.split(":")[0]
    for n in names:
        n_root = n.split(":")[0]
        if n == model or n.startswith(root + ":") or n_root == root:
            return True
    return False


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*\n?", text, re.IGNORECASE)
    if fence:
        text = text[fence.end() :]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].strip()
    return json.loads(text)


class TelosAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        backend: BackendName = "auto",
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        openai_model: str = "gpt-4o",
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.openai_model = openai_model
        self.ollama_base_url = (ollama_base_url or _ollama_base_url()).rstrip("/")
        self.ollama_model = ollama_model or _ollama_model()

        env_b = _env_backend()
        self.backend: BackendName = env_b if env_b is not None else backend

        self.system_prompt = """
        You are the Telos Framework Compiler Frontend.
        Your ONLY job is to translate human intent into strict JSON matching the TIR Schema.

        Rules for TIR JSON:
        - "ontology.bounds" must be a list of [min, max] arrays. Use [0.0, 1.0] for percentages.
        - "invariants.type" is "eq" (expression == 0) or "ineq" (expression >= 0).
        - To express "x must be less than 5", the ineq expression is "5 - x".
        - To express "x + y must equal 1", the eq expression is "x + y - 1.0".
        - Ensure constraints are mathematically sound algebraic expressions compatible with sympy.
        - Output ONLY valid JSON.
        """

    def _resolve_backend(self) -> BackendName:
        if self.backend != "auto":
            return self.backend
        if self.client:
            return "openai"
        if _ollama_reachable(self.ollama_base_url) and _ollama_model_installed(
            self.ollama_base_url, self.ollama_model
        ):
            return "ollama"
        return "mock"

    def translate(self, natural_language_input: str) -> TIRSchema:
        print(f"\n[Agent] Parsing English intent into TIR math...")

        resolved = self._resolve_backend()
        if resolved == "mock":
            if _ollama_reachable(self.ollama_base_url) and not _ollama_model_installed(
                self.ollama_base_url, self.ollama_model
            ):
                print(
                    "[Agent] WARNING: Ollama is running but model "
                    f"'{self.ollama_model}' is not installed. Using mock. "
                    f"Run: ollama pull {self.ollama_model.split(':')[0]}"
                )
            else:
                print(
                    "[Agent] WARNING: No OpenAI key and Ollama not ready "
                    f"({self.ollama_base_url}). Using mock translation for testing."
                )
            return self._mock_response()
        if resolved == "openai":
            return self._translate_openai(natural_language_input)
        if resolved == "ollama":
            print(
                f"[Agent] Using local Ollama ({self.ollama_model} @ {self.ollama_base_url})."
            )
            return self._translate_ollama(natural_language_input)
        return self._mock_response()

    def _translate_openai(self, natural_language_input: str) -> TIRSchema:
        if not self.client:
            raise RuntimeError("OpenAI backend selected but no API client (missing key).")

        response = self.client.chat.completions.create(
            model=self.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": natural_language_input},
            ],
            temperature=0.0,
        )

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI returned empty message content.")
        raw_json = json.loads(content)
        return TIRSchema(**raw_json)

    def _translate_ollama(self, natural_language_input: str) -> TIRSchema:
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": self.system_prompt.strip()},
                {"role": "user", "content": natural_language_input},
            ],
            "stream": False,
            "options": {"temperature": 0},
            "format": "json",
        }
        try:
            data = _http_json(url, payload)
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Ollama HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.ollama_base_url}. "
                "Is `ollama serve` running and the model pulled?"
            ) from e

        message = data.get("message") or {}
        content = message.get("content")
        if not content or not isinstance(content, str):
            raise RuntimeError(f"Unexpected Ollama response shape: {data!r}")

        raw_json = _extract_json_object(content)
        return TIRSchema(**raw_json)

    def _mock_response(self) -> TIRSchema:
        mock_data = {
            "ontology": {
                "variables": ["load_us", "load_eu", "load_asia"],
                "bounds": [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]],
            },
            "teleology": {
                "direction": "minimize",
                "objective": "10*load_us + 20*load_eu + 30*load_asia",
            },
            "invariants": [
                {"type": "eq", "expression": "load_us + load_eu + load_asia - 1.0"},
                {"type": "ineq", "expression": "0.4 - load_us"},
                {"type": "ineq", "expression": "0.05 - load_asia"},
            ],
        }
        return TIRSchema(**mock_data)
