from typing import Any, Literal
from pydantic import BaseModel, Field


RequestType = Literal[
    "case_resolution",
    "operational_recommendation",
    "chemical_analysis",
    "document_ingestion",
    "change_analysis",
    "change_apply",
    "sync_request",
]

ValidationLevel = Literal["standard", "strict", "critical"]
ActorRole = Literal["owner", "operator", "auditor", "admin", "system"]
ResponseStatus = Literal["ok", "blocked"]


class TranslateRequest(BaseModel):
    free_text: str = Field(..., min_length=5, description="Demande libre en langage naturel.")
    actor_role: ActorRole = "owner"
    target_language: str = "fr"
    audience: str = "internal"
    validation_level: ValidationLevel = "strict"
    context: dict[str, Any] = Field(default_factory=dict)


class ClarifyRequest(BaseModel):
    free_text: str = Field(..., min_length=5)
    current_governor_request: dict[str, Any] | None = None
    audience: str = "internal"
    context: dict[str, Any] = Field(default_factory=dict)


class ReformulateRequest(BaseModel):
    governor_output: dict[str, Any] = Field(..., description="Réponse JSON du gouverneur.")
    audience: str = "internal"
    tone: str = "professional"
    language: str = "fr"


class GovernorRequest(BaseModel):
    request_id: str | None = None
    request_type: RequestType
    actor_role: ActorRole = "owner"
    validation_level: ValidationLevel = "strict"
    source_text: str = ""
    needs_clarification: bool = False
    clarifying_questions: list[str] = Field(default_factory=list)
    entities: dict[str, Any] = Field(default_factory=dict)
    proposed_payload: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class GovernorExecutionResponse(BaseModel):
    status: ResponseStatus
    request_echo: GovernorRequest
    reformulation: str
    sufficiency: str
    impacted_zones: list[str] = Field(default_factory=list)
    blocking_questions: list[str] = Field(default_factory=list)
    proposed_changes: list[str] = Field(default_factory=list)
    files_or_tables: list[str] = Field(default_factory=list)
    tests_to_rerun: list[str] = Field(default_factory=list)
    raw_context: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    env: str
    llm_configured: bool
    supabase_configured: bool


class ErrorResponse(BaseModel):
    detail: str


class BookCreateResponse(BaseModel):
    book_id: str
    status: str
    filename: str
    chunks_created: int


class ExtractKnowledgeResponse(BaseModel):
    book_id: str
    chunks_processed: int
    rules_created: int
    status: str


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    book_id: str
    top_k: int = 5


class KnowledgeSearchResult(BaseModel):
    result_type: str
    chunk_id: str | None = None
    rule_id: str | None = None
    score: float | None = None
    content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    results: list[KnowledgeSearchResult] = Field(default_factory=list)
