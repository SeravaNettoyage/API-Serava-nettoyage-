from __future__ import annotations

from typing import Any

from supabase import Client, create_client

from app.core.settings import settings


class SupabaseService:
    def __init__(self) -> None:
        self.enabled = bool(settings.supabase_url and settings.supabase_service_role_key)
        self.client: Client | None = None
        if self.enabled:
            self.client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    def insert_audit(self, payload: dict[str, Any]) -> None:
        if not self.enabled or self.client is None:
            return
        try:
            self.client.schema(settings.supabase_schema).table(settings.audit_table).insert(payload).execute()
        except Exception:
            return

    def insert_book(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled or self.client is None:
            raise RuntimeError("Supabase non configuré")
        result = self.client.schema(settings.supabase_schema).table("books").insert(payload).execute()
        return result.data[0]

    def insert_book_chunks(self, rows: list[dict[str, Any]]) -> None:
        if not self.enabled or self.client is None:
            raise RuntimeError("Supabase non configuré")
        if rows:
            self.client.schema(settings.supabase_schema).table("book_chunks").insert(rows).execute()

    def update_book_status(self, book_id: str, status: str) -> None:
        if not self.enabled or self.client is None:
            raise RuntimeError("Supabase non configuré")
        self.client.schema(settings.supabase_schema).table("books").update({"status": status}).eq("id", book_id).execute()

    def get_book_chunks(self, book_id: str) -> list[dict[str, Any]]:
        if not self.enabled or self.client is None:
            raise RuntimeError("Supabase non configuré")
        result = (
            self.client.schema(settings.supabase_schema)
            .table("book_chunks")
            .select("*")
            .eq("book_id", book_id)
            .order("chunk_index")
            .execute()
        )
        return result.data or []

    def insert_knowledge_rules(self, rows: list[dict[str, Any]]) -> None:
        if not self.enabled or self.client is None:
            raise RuntimeError("Supabase non configuré")
        if rows:
            self.client.schema(settings.supabase_schema).table("knowledge_rules").insert(rows).execute()

    def search_book_chunks_ilike(self, book_id: str, terms: list[str], top_k: int) -> list[dict[str, Any]]:
        if not self.enabled or self.client is None:
            raise RuntimeError("Supabase non configuré")
        result = (
            self.client.schema(settings.supabase_schema)
            .table("book_chunks")
            .select("*")
            .eq("book_id", book_id)
            .limit(200)
            .execute()
        )
        rows = result.data or []
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in rows:
            content = (row.get("content") or "").lower()
            score = sum(content.count(term) for term in terms)
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for _, row in scored[:top_k]]

    def search_knowledge_rules_ilike(self, book_id: str, terms: list[str], top_k: int) -> list[dict[str, Any]]:
        if not self.enabled or self.client is None:
            raise RuntimeError("Supabase non configuré")
        result = (
            self.client.schema(settings.supabase_schema)
            .table("knowledge_rules")
            .select("*")
            .eq("book_id", book_id)
            .limit(500)
            .execute()
        )
        rows = result.data or []
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in rows:
            haystack = " ".join(
                str(row.get(key) or "")
                for key in ["rule_type", "surface", "fiber", "stain_type", "product", "equipment", "risk", "forbidden_action", "safety_notes", "expected_result", "source_quote"]
            ).lower()
            score = sum(haystack.count(term) for term in terms)
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for _, row in scored[:top_k]]
