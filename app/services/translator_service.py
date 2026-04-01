import json

from app.core.settings import settings
from app.models.contracts import (
    ClarifyRequest,
    GovernorRequest,
    ReformulateRequest,
    TranslateRequest,
)
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

TECHNICAL_LABEL_TRANSLATIONS = {
    "materiaux": "matériaux",
    "methodes": "méthodes",
    "produits": "produits",
    "decision_rules": "règles de décision",
    "validation_status": "statut de validation",
    "change_log": "journal des changements",
    "learning_documents": "documents d'apprentissage",
    "learning_claims": "assertions d'apprentissage",
    "chemical_entities": "entités chimiques",
    "canonical_guidance": "référentiel canonique",
    "problemes": "problèmes",
    "equipements": "équipements",
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

    def _normalize_result(
        self,
        data: dict,
        source_text: str,
        actor_role: str,
        validation_level: str,
    ) -> dict:
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

    def _translate_label(self, value: str) -> str:
        if not isinstance(value, str):
            return str(value)
        return TECHNICAL_LABEL_TRANSLATIONS.get(value, value)

    def _translate_labels(self, values):
        if not isinstance(values, list):
            return []
        return [self._translate_label(str(v)) for v in values if v is not None]

    def _format_list(self, items):
        if not isinstance(items, list):
            return ""

        cleaned = [str(item).strip() for item in items if str(item).strip()]
        if not cleaned:
            return ""

        if len(cleaned) == 1:
            return cleaned[0]

        if len(cleaned) == 2:
            return f"{cleaned[0]} et {cleaned[1]}"

        return ", ".join(cleaned[:-1]) + f" et {cleaned[-1]}"

    def _request_type_label(self, request_type: str) -> str:
        mapping = {
            "case_resolution": "résolution de cas",
            "operational_recommendation": "recommandation opérationnelle",
            "chemical_analysis": "analyse chimique",
            "document_ingestion": "ingestion documentaire",
            "change_analysis": "analyse de changement",
            "change_apply": "application de changement",
            "sync_request": "demande de synchronisation",
        }
        return mapping.get(request_type, request_type)

    def _deterministic_reformulation(self, governor_output: dict) -> str:
        if not isinstance(governor_output, dict):
            return "Aucune donnée exploitable n'a été fournie."

        request_echo = governor_output.get("request_echo") or {}
        raw_context = governor_output.get("raw_context") or {}

        validation_level = request_echo.get("validation_level", "standard")
        request_type = self._request_type_label(request_echo.get("request_type", "inconnu"))
        sufficiency = governor_output.get("sufficiency", "")
        impacted_zones = self._translate_labels(governor_output.get("impacted_zones", []))
        proposed_changes = self._ensure_list_of_strings(governor_output.get("proposed_changes", []))
        files_or_tables = self._translate_labels(governor_output.get("files_or_tables", []))
        tests_to_rerun = self._ensure_list_of_strings(governor_output.get("tests_to_rerun", []))
        blocking_questions = self._ensure_list_of_strings(governor_output.get("blocking_questions", []))

        paragraphs = []

        intro = f"Demande traitée en mode {validation_level} pour une {request_type}."
        if sufficiency:
            sufficiency_mapping = {
                "sufficient": "Les informations disponibles sont suffisantes.",
                "insufficient_information": "Les informations disponibles sont insuffisantes.",
                "blocked_by_policy": "Le traitement est bloqué par la politique actuelle.",
            }
            extra = sufficiency_mapping.get(sufficiency, "")
            if extra:
                intro += f" {extra}"
        paragraphs.append(intro.strip())

        if impacted_zones:
            paragraphs.append(f"Zones impactées : {self._format_list(impacted_zones)}.")

        if proposed_changes:
            paragraphs.append(f"Actions proposées : {self._format_list(proposed_changes)}.")

        if files_or_tables:
            paragraphs.append(f"Fichiers ou tables concernés : {self._format_list(files_or_tables)}.")

        if tests_to_rerun:
            label = "Test à relancer" if len(tests_to_rerun) == 1 else "Tests à relancer"
            paragraphs.append(f"{label} : {self._format_list(tests_to_rerun)}.")

        if blocking_questions:
            label = "Question bloquante" if len(blocking_questions) == 1 else "Questions bloquantes"
            paragraphs.append(f"{label} : {self._format_list(blocking_questions)}.")

        if raw_context.get("policy_mutations_enabled") is False:
            paragraphs.append("Les mutations sont désactivées par la politique actuelle.")

        return "\\n\\n".join(paragraphs).strip()

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
        text = self._deterministic_reformulation(data.governor_output)
        return {"text": text}
