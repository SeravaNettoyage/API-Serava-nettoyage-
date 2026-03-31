import json

from app.core.settings import settings
from app.models.contracts import GovernorRequest, TranslateRequest, ClarifyRequest, ReformulateRequest
from app.services.llm_client import LLMClient
from app.services.prompt_loader import load_prompt


REQUEST_TYPE_ALIASES = {
    "impact_analysis": "change_analysis",
    "impact_study": "change_analysis",
    "change_impact_analysis": "change_analysis",
    "recommendation": "operational_recommendation",
    "case_analysis": "case_resolution",
    "chemical_review": "chemical_analysis",
    "document_analysis": "document_ingestion",
}


class TranslatorService:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _ensure_dict(self, value):
        return value if isinstance(value, dict) else {}

    def _ensure_list_of_strings(self, value):
        if not isinstance(value, list):
            return []
        return [str(x) for x in value if x is not None]

    def _ensure_bool(self, value):
        return bool(value)

    def _normalize_request_type(self, value: str) -> str:
        if not isinstance(value, str):
            return "case_resolution"
        normalized = value.strip().lower()
        return REQUEST_TYPE_ALIASES.get(normalized, normalized)

    def _normalize_result(self, data: dict, source_text: str, actor_role: str, validation_level: str) -> dict:
        if not isinstance(data, dict):
            data = {}

        data["request_type"] = self._normalize_request_type(data.get("request_type"))
        data["actor_role"] = data.get("actor_role") if isinstance(data.get("actor_role"), str) else actor_role
        data["validation_level"] = (
            data.get("validation_level") if isinstance(data.get("validation_level"), str) else validation_level
        )
        data["source_text"] = data.get("source_text") if isinstance(data.get("source_text"), str) else source_text
        data["needs_clarification"] = self._ensure_bool(data.get("needs_clarification", False))
        data["clarifying_questions"] = self._ensure_list_of_strings(data.get("clarifying_questions", []))
        data["entities"] = self._ensure_dict(data.get("entities", {}))
        data["proposed_payload"] = self._ensure_dict(data.get("proposed_payload", {}))
        data["context"] = self._ensure_dict(data.get("context", {}))

        return data

    async def translate(self, data: TranslateRequest) -> GovernorRequest:
        prompt = load_prompt("translator")
        user_prompt = json.dumps(data.model_dump(mode="json"), ensure_ascii=False)
        result = await self.llm.chat_json(prompt, user_prompt, settings.llm_model_translate)
        result = self._normalize_result(
            result,
            source_text=data.free_text,
            actor_role=data.actor_role,
            validation_level=data.validation_level,
        )
        return GovernorRequest.model_validate(result)

    async def clarify(self, data: ClarifyRequest) -> dict:
        prompt = load_prompt("clarifier")
        user_prompt = json.dumps(data.model_dump(mode="json"), ensure_ascii=False)
        return await self.llm.chat_json(prompt, user_prompt, settings.llm_model_clarify)

    async def reformulate(self, data: ReformulateRequest) -> dict:
        prompt = load_prompt("reformulator")
        user_prompt = json.dumps(data.model_dump(mode="json"), ensure_ascii=False)
        text = await self.llm.chat_text(prompt, user_prompt, settings.llm_model_reformulate)
        return {"text": text}
