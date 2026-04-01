from uuid import uuid4

from app.core.settings import settings
from app.models.contracts import GovernorRequest, GovernorExecutionResponse
from app.services.supabase_client import SupabaseService


REQUEST_TYPE_LABELS = {
    "case_resolution": "résolution de cas",
    "operational_recommendation": "recommandation opérationnelle",
    "chemical_analysis": "analyse chimique",
    "document_ingestion": "ingestion documentaire",
    "change_analysis": "analyse de changement",
    "change_apply": "application de changement",
    "sync_request": "demande de synchronisation",
}


class GovernorService:
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service

    def _build_operational_recommendation_response(
        self,
        request_obj: GovernorRequest,
        status: str,
        sufficiency: str,
        blocked: list[str],
    ) -> GovernorExecutionResponse:
        entities = request_obj.entities or {}
        proposed_payload = request_obj.proposed_payload or {}

        company = entities.get("company")
        product_lines = entities.get("product_lines", [])
        constraint = entities.get("constraint")
        decision_scope = proposed_payload.get("decision_scope")
        options = proposed_payload.get("options", [])

        impacted = ["produits", "methodes", "decision_rules"]
        files_or_tables = impacted.copy()

        proposed = []

        if decision_scope == "launch_priority":
            proposed.append("comparer les options de lancement selon le coût d'acquisition et la simplicité opérationnelle")
            proposed.append("prioriser l'offre la plus facile à vendre avec un budget marketing limité")
            proposed.append("préparer un test terrain avant déploiement élargi")
        else:
            proposed.append("analyser les options disponibles")
            proposed.append("évaluer les contraintes opérationnelles et commerciales")
            proposed.append("retenir l'option la plus robuste")

        if company:
            impacted.append("change_log")

        rerun = ["operational_recommendation_smoke_test"]

        reformulation = (
            f"Demande de recommandation opérationnelle traitée en mode {request_obj.validation_level} "
            f"pour {company or 'l’activité'}. "
            f"Options étudiées : {', '.join(options) if options else ', '.join(product_lines) if product_lines else 'non précisées'}."
        )

        raw_context = {
            "policy_mutations_enabled": settings.allow_governor_mutations,
            "company": company,
            "constraint": constraint,
            "decision_scope": decision_scope,
        }

        return GovernorExecutionResponse(
            status=status,
            request_echo=request_obj,
            reformulation=reformulation,
            sufficiency=sufficiency,
            impacted_zones=impacted,
            blocking_questions=blocked,
            proposed_changes=proposed,
            files_or_tables=files_or_tables,
            tests_to_rerun=rerun,
            raw_context=raw_context,
        )

    def _build_case_resolution_response(
        self,
        request_obj: GovernorRequest,
        status: str,
        sufficiency: str,
        blocked: list[str],
    ) -> GovernorExecutionResponse:
        impacted = ["materiaux", "methodes", "produits", "problemes", "equipements", "decision_rules"]
        files_or_tables = impacted.copy()
        proposed = [
            "reformuler le cas",
            "poser les questions diagnostiques",
            "proposer des pré-tests, les risques et la voie prudente",
        ]
        rerun = ["case_reasoning_smoke_test"]

        return GovernorExecutionResponse(
            status=status,
            request_echo=request_obj,
            reformulation=f"Demande traitée en mode {request_obj.validation_level} pour une résolution de cas.",
            sufficiency=sufficiency,
            impacted_zones=impacted,
            blocking_questions=blocked,
            proposed_changes=proposed,
            files_or_tables=files_or_tables,
            tests_to_rerun=rerun,
            raw_context={"policy_mutations_enabled": settings.allow_governor_mutations},
        )

    def _build_chemical_response(
        self,
        request_obj: GovernorRequest,
        status: str,
        sufficiency: str,
        blocked: list[str],
    ) -> GovernorExecutionResponse:
        impacted = ["learning_documents", "learning_claims", "chemical_entities", "canonical_guidance"]
        files_or_tables = impacted.copy()
        proposed = [
            "extraire les composants",
            "lier les composants aux entités métier",
            "détecter les conflits ou incompatibilités",
        ]
        rerun = ["chemistry_parse_test"]

        return GovernorExecutionResponse(
            status=status,
            request_echo=request_obj,
            reformulation=f"Demande traitée en mode {request_obj.validation_level} pour une analyse chimique ou documentaire.",
            sufficiency=sufficiency,
            impacted_zones=impacted,
            blocking_questions=blocked,
            proposed_changes=proposed,
            files_or_tables=files_or_tables,
            tests_to_rerun=rerun,
            raw_context={"policy_mutations_enabled": settings.allow_governor_mutations},
        )

    def _build_change_response(
        self,
        request_obj: GovernorRequest,
        status: str,
        sufficiency: str,
        blocked: list[str],
    ) -> GovernorExecutionResponse:
        impacted = ["materiaux", "methodes", "produits", "decision_rules", "validation_status", "change_log"]
        files_or_tables = impacted.copy()
        proposed = [
            "analyser les dépendances",
            "synchroniser les dérivés",
            "rejouer les cas impactés",
        ]
        rerun = ["master_sync_regression"]

        return GovernorExecutionResponse(
            status=status,
            request_echo=request_obj,
            reformulation=f"Demande traitée en mode {request_obj.validation_level} pour une analyse ou application de changement.",
            sufficiency=sufficiency,
            impacted_zones=impacted,
            blocking_questions=blocked,
            proposed_changes=proposed,
            files_or_tables=files_or_tables,
            tests_to_rerun=rerun,
            raw_context={"policy_mutations_enabled": settings.allow_governor_mutations},
        )

    async def execute(self, req: GovernorRequest) -> GovernorExecutionResponse:
        request_id = req.request_id or str(uuid4())
        request_obj = req.model_copy(update={"request_id": request_id})

        blocked: list[str] = []
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

        if request_obj.request_type == "operational_recommendation":
            response = self._build_operational_recommendation_response(
                request_obj=request_obj,
                status=status,
                sufficiency=sufficiency,
                blocked=blocked,
            )
        elif request_obj.request_type == "case_resolution":
            response = self._build_case_resolution_response(
                request_obj=request_obj,
                status=status,
                sufficiency=sufficiency,
                blocked=blocked,
            )
        elif request_obj.request_type in {"chemical_analysis", "document_ingestion"}:
            response = self._build_chemical_response(
                request_obj=request_obj,
                status=status,
                sufficiency=sufficiency,
                blocked=blocked,
            )
        elif request_obj.request_type in {"change_analysis", "change_apply", "sync_request"}:
            response = self._build_change_response(
                request_obj=request_obj,
                status=status,
                sufficiency=sufficiency,
                blocked=blocked,
            )
        else:
            response = GovernorExecutionResponse(
                status=status,
                request_echo=request_obj,
                reformulation=f"Demande traitée en mode {request_obj.validation_level} pour le type {request_obj.request_type}.",
                sufficiency=sufficiency,
                impacted_zones=[],
                blocking_questions=blocked,
                proposed_changes=[],
                files_or_tables=[],
                tests_to_rerun=[],
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
