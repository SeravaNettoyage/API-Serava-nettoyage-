from __future__ import annotations

import re

from app.core.settings import settings
from app.services.supabase_client import SupabaseService


class RetrievalService:
    def __init__(self, supabase: SupabaseService):
        self.supabase = supabase

    def _normalize_terms(self, query: str) -> list[str]:
        terms = re.findall(r"[a-zA-ZÀ-ÿ0-9']+", query.lower())
        return [t for t in terms if len(t) >= 3]

    def search(self, book_id: str, query: str, top_k: int | None = None) -> dict[str, list[dict]]:
        top_k = top_k or settings.retrieval_default_top_k
        terms = self._normalize_terms(query)
        if not terms:
            return {'chunks': [], 'rules': []}
        return {
            'chunks': self.supabase.search_book_chunks_ilike(book_id, terms, top_k),
            'rules': self.supabase.search_knowledge_rules_ilike(book_id, terms, top_k),
        }
