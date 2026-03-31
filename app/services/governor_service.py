from uuid import uuid4

from app.core.settings import settings
from app.models.contracts import GovernorRequest, GovernorExecutionResponse
from app.services.supabase_client import SupabaseService


class GovernorService:
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service

    async def execute(self, req: GovernorRequest) -> GovernorExecutionResponse:
        request_id = req.request_id or str(uuid4())
        request_obj = req.model_copy(update={"request_id": request_id})

        blocked: list[str] = []
        impacted: list[str] = []
        proposed: list[str] = []
        rerun: list[str] = []
        files_or_tables: list[str] = []
        sufficiency = "sufficient"
        status = "ok"

        if request_obj.request_type in {"change_apply", "sync_request"} and not settings.allow_governor_mutations:
            status = "blocked"
            sufficiency = "blocked_by_policy"
            blocked.append("Les mutations sont désactivées par configuration API.")

        if request_obj.needs_clarification or request_obj.clarifying_questions:
            status = "blocked"
            sufficiency = "insufficient_information"
            blocked.extend(request_obj.clarifying_questions)

        if request_obj.request_type in {"case_resolution", "operational_recommendation"}:
            impacted = ["materiaux", "methodes", "produits", "problemes", "equipements", "decision_rules"]
            files_or_tables = impacted.copy()
            proposed = [
                "reformuler le cas",
                "poser les questions diagnostiques",
                "proposer des pré-tests, les risques et la voie prudente",
            ]
            rerun = ["case_reasoning_smoke_test"]
        elif request_obj.request_type in {"chemical_analysis", "document_ingestion"}:
            impacted = ["learning_documents", "learning_claims", "chemical_entities", "canonical_guidance"]
            files_or_tables = impacted.copy()
            proposed = ["extraire les composants", "lier aux entités métier", "détecter les conflits"]
            rerun = ["chemistry_parse_test"]
        elif request_obj.request_type in {"change_analysis", "change_apply", "sync_request"}:
            impacted = ["materiaux", "methodes", "produits", "decision_rules", "validation_status", "change_log"]
            files_or_tables = impacted.copy()
            proposed = ["analyser les dépendances", "synchroniser les dérivés", "rejouer les cas impactés"]
            rerun = ["master_sync_regression"]

        response = GovernorExecutionResponse(
            status=status,
            request_echo=request_obj,
            reformulation=f"Demande traitée en mode {request_obj.validation_level} pour le type {request_obj.request_type}.",
            sufficiency=sufficiency,
            impacted_zones=impacted,
            blocking_questions=blocked,
            proposed_changes=proposed,
            files_or_tables=files_or_tables,
            tests_to_rerun=rerun,
            raw_context={"policy_mutations_enabled": settings.allow_governor_mutations},
        )

        self.supabase.insert_audit(
            {
                "request_id": request_obj.request_id,
                "request_type": request_obj.request_type,
                "status": response.status,
                "actor_role": request_obj.actor_role,
                "payload": request_obj.model_dump(mode="json"),
                "response": response.model_dump(mode="json"),
            }
        )
        return response
