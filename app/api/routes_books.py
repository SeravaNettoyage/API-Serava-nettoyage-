from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.routes import require_api_key
from app.models.contracts import (
    BookCreateResponse,
    ExtractKnowledgeResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
)
from app.services.book_ingestion_service import BookIngestionService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.llm_client import LLMClient
from app.services.retrieval_service import RetrievalService
from app.services.supabase_client import SupabaseService

router_books = APIRouter(tags=['books'])

supabase_service = SupabaseService()
llm_client = LLMClient()
book_ingestion_service = BookIngestionService(supabase_service)
knowledge_extraction_service = KnowledgeExtractionService(llm_client, supabase_service)
retrieval_service = RetrievalService(supabase_service)


@router_books.post('/books/upload', response_model=BookCreateResponse, dependencies=[Depends(require_api_key)])
async def upload_book(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    author: str | None = Form(default=None),
):
    try:
        content = await file.read()
        book_id, chunks_created = book_ingestion_service.ingest_pdf(
            filename=file.filename or 'book.pdf',
            file_bytes=content,
            title=title,
            author=author,
        )
        return BookCreateResponse(
            book_id=book_id,
            status='chunked',
            filename=file.filename or 'book.pdf',
            chunks_created=chunks_created,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Échec d’ingestion du livre: {exc}') from exc


@router_books.post('/books/{book_id}/extract', response_model=ExtractKnowledgeResponse, dependencies=[Depends(require_api_key)])
async def extract_book(book_id: str):
    try:
        chunks_processed, rules_created = await knowledge_extraction_service.extract_book(book_id)
        return ExtractKnowledgeResponse(
            book_id=book_id,
            chunks_processed=chunks_processed,
            rules_created=rules_created,
            status='extracted',
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Échec d’extraction des connaissances: {exc}') from exc


@router_books.post('/knowledge/search', response_model=KnowledgeSearchResponse, dependencies=[Depends(require_api_key)])
async def search_knowledge(payload: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    try:
        results = retrieval_service.search(payload.book_id, payload.query, payload.top_k)
        items: list[KnowledgeSearchResult] = []
        for chunk in results['chunks']:
            items.append(
                KnowledgeSearchResult(
                    result_type='chunk',
                    chunk_id=chunk.get('id'),
                    score=None,
                    content=chunk.get('content'),
                    metadata={
                        'chunk_index': chunk.get('chunk_index'),
                        'source_ref': chunk.get('source_ref'),
                    },
                )
            )
        for rule in results['rules']:
            items.append(
                KnowledgeSearchResult(
                    result_type='rule',
                    rule_id=rule.get('id'),
                    score=None,
                    content=rule.get('source_quote') or rule.get('expected_result'),
                    metadata={
                        'rule_type': rule.get('rule_type'),
                        'surface': rule.get('surface'),
                        'stain_type': rule.get('stain_type'),
                        'product': rule.get('product'),
                        'risk': rule.get('risk'),
                    },
                )
            )
        return KnowledgeSearchResponse(results=items)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Échec de recherche documentaire: {exc}') from exc
