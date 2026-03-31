from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.settings import settings
from app.models.contracts import (
    ClarifyRequest,
    GovernorExecutionResponse,
    GovernorRequest,
    HealthResponse,
    ReformulateRequest,
    TranslateRequest,
)
from app.services.governor_service import GovernorService
from app.services.llm_client import LLMClient
from app.services.supabase_client import SupabaseService
from app.services.translator_service import TranslatorService

router = APIRouter()

llm_client = LLMClient()
supabase_service = SupabaseService()
translator_service = TranslatorService(llm_client)
governor_service = GovernorService(supabase_service)


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    expected_key = settings.internal_api_key

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clé API interne non configurée sur le serveur.",
        )

    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou absente.",
        )


@router.get("/", tags=["system"])
async def root() -> dict:
    return {"message": "Serava API running"}


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
        llm_configured=bool(settings.llm_api_key),
        supabase_configured=bool(settings.supabase_url and settings.supabase_service_role_key),
    )


@router.post("/translate", response_model=GovernorRequest, tags=["governor"], dependencies=[Depends(require_api_key)])
async def translate(payload: TranslateRequest) -> GovernorRequest:
    try:
        return await translator_service.translate(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Échec de translation: {exc}") from exc


@router.post("/clarify", tags=["governor"], dependencies=[Depends(require_api_key)])
async def clarify(payload: ClarifyRequest) -> dict:
    try:
        return await translator_service.clarify(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Échec de clarification: {exc}") from exc


@router.post(
    "/governor/execute",
    response_model=GovernorExecutionResponse,
    tags=["governor"],
    dependencies=[Depends(require_api_key)],
)
async def execute_governor(payload: GovernorRequest) -> GovernorExecutionResponse:
    try:
        return await governor_service.execute(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Échec d'exécution gouverneur: {exc}") from exc


@router.post("/reformulate", tags=["governor"], dependencies=[Depends(require_api_key)])
async def reformulate(payload: ReformulateRequest) -> dict:
    try:
        return await translator_service.reformulate(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Échec de reformulation: {exc}") from exc
