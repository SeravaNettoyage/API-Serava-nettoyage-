from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Serava Governor Backend"
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 8000

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_schema: str = "public"

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model_translate: str = "gpt-4.1-mini"
    llm_model_clarify: str = "gpt-4.1-mini"
    llm_model_reformulate: str = "gpt-4.1-mini"
    llm_timeout_seconds: int = 45

    allow_governor_mutations: bool = False
    default_canonical_language: str = "fr"
    default_audience: str = "internal"


settings = Settings()
