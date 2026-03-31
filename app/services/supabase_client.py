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
            # Intentionnellement silencieux pour ne pas bloquer l'API métier
            return
