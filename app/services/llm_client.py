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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if "openrouter.ai" in self.base_url:
            if settings.llm_openrouter_referer:
                headers["HTTP-Referer"] = settings.llm_openrouter_referer
            if settings.llm_openrouter_title:
                headers["X-Title"] = settings.llm_openrouter_title

        return headers

    def _extract_content_from_chat_response(self, data: dict) -> str:
        if not isinstance(data, dict):
            raise RuntimeError("Réponse LLM invalide: format non JSON exploitable")

        # Cas erreur standard OpenRouter
        if "error" in data and isinstance(data["error"], dict):
            message = data["error"].get("message", "Erreur LLM inconnue")
            code = data["error"].get("code")
            raise RuntimeError(f"Erreur OpenRouter ({code}): {message}")

        # Cas nominal OpenAI/OpenRouter Chat Completions
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content")

            if isinstance(content, str):
                return content

            # Certains formats peuvent retourner un contenu structuré en liste
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        text_value = item.get("text")
                        if isinstance(text_value, str):
                            parts.append(text_value)
                if parts:
                    return "\n".join(parts)

        raise RuntimeError(f"Réponse LLM inattendue: {json.dumps(data, ensure_ascii=False)[:1200]}")

    async def chat_json(self, system_prompt: str, user_prompt: str, model: str) -> dict:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": settings.llm_temperature,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )

            # On essaie d'extraire le JSON même en cas d'erreur
            try:
                data = response.json()
            except Exception:
                response.raise_for_status()
                raise RuntimeError("Réponse LLM non lisible en JSON")

            if response.status_code >= 400:
                if isinstance(data, dict) and "error" in data:
                    err = data["error"]
                    message = err.get("message", "Erreur LLM inconnue")
                    code = err.get("code", response.status_code)
                    raise RuntimeError(f"Erreur OpenRouter ({code}): {message}")
                response.raise_for_status()

            content = self._extract_content_from_chat_response(data)

            try:
                return json.loads(content)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Le modèle n'a pas renvoyé un JSON valide: {content[:1000]}") from exc

    async def chat_text(self, system_prompt: str, user_prompt: str, model: str) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": settings.llm_temperature,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )

            try:
                data = response.json()
            except Exception:
                response.raise_for_status()
                raise RuntimeError("Réponse LLM non lisible en JSON")

            if response.status_code >= 400:
                if isinstance(data, dict) and "error" in data:
                    err = data["error"]
                    message = err.get("message", "Erreur LLM inconnue")
                    code = err.get("code", response.status_code)
                    raise RuntimeError(f"Erreur OpenRouter ({code}): {message}")
                response.raise_for_status()

            return self._extract_content_from_chat_response(data)
