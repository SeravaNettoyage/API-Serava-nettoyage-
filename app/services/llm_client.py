import json
import httpx

from app.core.settings import settings


class LLMClient:
    def __init__(self) -> None:
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.timeout = settings.llm_timeout_seconds

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY manquant")

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _extract_content_from_chat_response(self, data: dict) -> str:
        if isinstance(data, dict) and "error" in data:
            error = data["error"]
            if isinstance(error, dict):
                message = error.get("message", "Erreur LLM inconnue")
                code = error.get("code", "unknown")
                raise RuntimeError(f"Erreur OpenRouter ({code}): {message}")
            raise RuntimeError(f"Erreur LLM: {json.dumps(data, ensure_ascii=False)}")

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content")

            if isinstance(content, str):
                return content

            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        text_value = item.get("text")
                        if isinstance(text_value, str):
                            parts.append(text_value)
                if parts:
                    return "\n".join(parts)

        raise RuntimeError(
            f"Réponse LLM inattendue: {json.dumps(data, ensure_ascii=False)[:1200]}"
        )

    async def chat_json(self, system_prompt: str, user_prompt: str, model: str) -> dict:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
            except httpx.HTTPError as exc:
                raise RuntimeError(f"Erreur réseau LLM: {exc}") from exc

        try:
            data = response.json()
        except Exception as exc:
            raise RuntimeError(f"Réponse LLM non JSON: {response.text}") from exc

        if response.status_code >= 400:
            if isinstance(data, dict) and "error" in data:
                err = data["error"]
                if isinstance(err, dict):
                    message = err.get("message", "Erreur LLM inconnue")
                    code = err.get("code", response.status_code)
                    raise RuntimeError(f"Erreur OpenRouter ({code}): {message}")
            raise RuntimeError(f"Erreur LLM HTTP {response.status_code}: {response.text}")

        content = self._extract_content_from_chat_response(data)

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Le modèle n'a pas renvoyé un JSON valide: {content[:1000]}"
            ) from exc

    async def chat_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
            except httpx.HTTPError as exc:
                raise RuntimeError(f"Erreur réseau LLM: {exc}") from exc

        try:
            data = response.json()
        except Exception as exc:
            raise RuntimeError(f"Réponse LLM non JSON: {response.text}") from exc

        if response.status_code >= 400:
            if isinstance(data, dict) and "error" in data:
                err = data["error"]
                if isinstance(err, dict):
                    message = err.get("message", "Erreur LLM inconnue")
                    code = err.get("code", response.status_code)
                    raise RuntimeError(f"Erreur OpenRouter ({code}): {message}")
            raise RuntimeError(f"Erreur LLM HTTP {response.status_code}: {response.text}")

        return self._extract_content_from_chat_response(data)
