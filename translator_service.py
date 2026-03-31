import json
from app.core.settings import settings
from app.models.contracts import GovernorRequest, TranslateRequest, ClarifyRequest, ReformulateRequest
from app.services.llm_client import LLMClient
from app.services.prompt_loader import load_prompt


class TranslatorService:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def translate(self, data: TranslateRequest) -> GovernorRequest:
        prompt = load_prompt("translator")
        user_prompt = json.dumps(data.model_dump(mode="json"), ensure_ascii=False)
        result = await self.llm.chat_json(prompt, user_prompt, settings.llm_model_translate)
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
