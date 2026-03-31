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

    def _normalize_request_type(self, data: dict) -> dict:
        value = data.get("request_type")
        if isinstance(value, str):
            normalized = REQUEST_TYPE_ALIASES.get(value.strip().lower(), value.strip().lower())
            data["request_type"] = normalized
        return data

    async def translate(self, data: TranslateRequest) -> GovernorRequest:
        prompt = load_prompt("translator")
        user_prompt = json.dumps(data.model_dump(mode="json"), ensure_ascii=False)
        result = await self.llm.chat_json(prompt, user_prompt, settings.llm_model_translate)
        result = self._normalize_request_type(result)
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
