from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Serava Governor Backend"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_version: str = "1.1.0"
    docs_enabled: bool = True

    api_key_header_name: str = "X-API-Key"
    internal_api_key: str = ""

    cors_allow_origins: str = "*"
    cors_allow_methods: str = "GET,POST,OPTIONS"
    cors_allow_headers: str = "*"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_schema: str = "public"
    audit_table: str = "governor_audit"

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model_translate: str = "gpt-4.1-mini"
    llm_model_clarify: str = "gpt-4.1-mini"
    llm_model_reformulate: str = "gpt-4.1-mini"
    llm_timeout_seconds: int = 45
    llm_temperature: float = 0.1
    llm_model_extract: str = "gpt-4.1-mini"
    llm_model_governor: str = "gpt-4.1-mini"
    llm_openrouter_referer: str = ""
    llm_openrouter_title: str = "Serava Governor Backend"

    allow_governor_mutations: bool = False
    default_canonical_language: str = "fr"
    default_audience: str = "internal"

    request_log_payloads: bool = True

    chunk_max_chars: int = 3500
    chunk_overlap_chars: int = 400
    retrieval_default_top_k: int = 5

    @property
    def cors_allow_origins_list(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [x.strip() for x in self.cors_allow_origins.split(",") if x.strip()]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return [x.strip() for x in self.cors_allow_methods.split(",") if x.strip()]

    @property
    def cors_allow_headers_list(self) -> list[str]:
        if self.cors_allow_headers.strip() == "*":
            return ["*"]
        return [x.strip() for x in self.cors_allow_headers.split(",") if x.strip()]


settings = Settings()
