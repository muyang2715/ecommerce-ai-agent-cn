"""Crate 中文电商智能客服配置。"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4o"
    temperature: float = 0.0

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Langfuse Observability (optional — set to enable tracing)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
