from __future__ import annotations
import os, json, subprocess, urllib.request, urllib.error
from typing import Optional


class LLM:
    """
    Minimal LLM wrapper (stdlib only).
    Tests monkeypatch this class, so keep interface stable.
    """

    def __init__(self, backend: str = "ollama", timeout_s: int = 60):
        self.backend = backend.lower()
        self.timeout_s = timeout_s

    def complete(self, prompt: str) -> str:
        if self.backend == "ollama":
            return self._ollama(prompt)
        if self.backend == "groq":
            return self._groq(prompt)
        if self.backend == "gemini":
            return self._gemini(prompt)
        raise ValueError("backend must be 'ollama', 'groq', or 'gemini'")

    def _ollama(self, prompt: str) -> str:
        model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Try chat API first
        url = f"{base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.2,
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Ollama request failed: {e}\n"
                f"Make sure Ollama is running at {base_url}\n"
                f"Start Ollama: ollama serve\n"
                f"Pull model: ollama pull {model}"
            ) from e
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode()
            except:
                pass
            raise RuntimeError(
                f"Ollama HTTP {e.code}: {err_body}\n"
                f"Make sure model '{model}' is installed.\n"
                f"Pull model: ollama pull {model}"
            ) from e
        
        obj = json.loads(raw)
        msg = obj.get("message", {})
        response = msg.get("content", "").strip() if isinstance(msg, dict) else ""
        if not response:
            raise RuntimeError(f"Ollama empty response: {obj}")
        return response

    def _groq(self, prompt: str) -> str:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set")

        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            raise RuntimeError(f"Groq HTTPError: {e.code} - {err_body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Groq request failed: {e}") from e

        obj = json.loads(raw)

        if "choices" not in obj:
            raise RuntimeError(f"Groq error response: {obj}")

        return obj["choices"][0]["message"]["content"].strip()

    def _gemini(self, prompt: str) -> str:
        raise NotImplementedError("Gemini backend not implemented yet")
