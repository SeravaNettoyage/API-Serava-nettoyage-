from __future__ import annotations

import json
import uuid

from app.core.settings import settings
from app.models.contracts import GovernorExecutionResponse, GovernorRequest
from app.services.llm_client import LLMClient
from app.services.prompt_loader import load_prompt
from app.services.retrieval_service import RetrievalService
from app.services.supabase_client import SupabaseService


class GovernorService:
    def __init__(self, supabase: SupabaseService, llm_client: LLMClient | None = None) -> None:
        self.supabase = supabase
        self.llm_client = llm_client or LLMClient()
        self.retrieval_service = RetrievalService(supabase)

    async def execute(self, payload: GovernorRequest) -> GovernorExecutionResponse:
        request_id = payload.request_id or str(uuid.uuid4())
        payload.request_id = request_id

        book_id = str(payload.context.get("book_id") or payload.entities.get("book_id") or "")
        retrieval_context: dict = {"chunks": [], "rules": []}

        if book_id and self.supabase.enabled:
            try:
                retrieval_context = self.retrieval_service.search(
                    book_id=book_id,
                    query=payload.source_text or json.dumps(payload.proposed_payload, ensure_ascii=False),
                    top_k=settings.retrieval_default_top_k,
                )
            except Exception as e:
                # Fallback: log error but continue without retrieval
                retrieval_context = {"chunks": [], "rules": [], "error": str(e)}

        if payload.needs_clarification or payload.clarifying_questions:
            response = GovernorExecutionResponse(
                status="blocked",
                request_echo=payload,
                reformulation="Des informations complémentaires sont nécessaires avant exécution.",
                sufficiency="insufficient",
                blocking_questions=payload.clarifying_questions,
                raw_context={"retrieval": retrieval_context},
            )
            self._audit(payload, response)
            return response

        if retrieval_context["chunks"] or retrieval_context["rules"]:
            system_prompt = load_prompt("governor_knowledge")
            user_prompt = json.dumps(
                {
                    "request": payload.model_dump(),
                    "retrieval": retrieval_context,
                },
                ensure_ascii=False,
            )
            llm_output = await self.llm_client.chat_json(system_prompt, user_prompt, settings.llm_model_governor)
            response = GovernorExecutionResponse.model_validate({"request_echo": payload, **llm_output})
            response.raw_context = {"retrieval": retrieval_context}
        else:
            response = GovernorExecutionResponse(
                status="ok",
                request_echo=payload,
                reformulation="Aucune base documentaire rattachée n’a été trouvée. Réponse conservatrice générée sans moteur documentaire.",
                sufficiency="partial",
                impacted_zones=["governor", "knowledge_base"],
                proposed_changes=["Rattacher un book_id valide dans context.book_id ou entities.book_id."],
                files_or_tables=["books", "book_chunks", "knowledge_rules"],
                tests_to_rerun=["POST /books/upload", "POST /books/{book_id}/extract", "POST /governor/execute"],
                raw_context={"retrieval": retrieval_context},
            )

        self._audit(payload, response)
        return response

    def _audit(self, payload: GovernorRequest, response: GovernorExecutionResponse) -> None:
        self.supabase.insert_audit(
            {
                "request_id": payload.request_id,
                "request_type": payload.request_type,
                "actor_role": payload.actor_role,
                "validation_level": payload.validation_level,
                "status": response.status,
                "sufficiency": response.sufficiency,
                "request_payload": payload.model_dump() if settings.request_log_payloads else {},
                "response_payload": response.model_dump() if settings.request_log_payloads else {},
            }
        )
