"""
Configuração centralizada do projeto Site Workflow v2.2.
Gerencia variáveis de ambiente e diretórios do projeto.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from rich.console import Console
from rich.table import Table


class Settings(BaseSettings):
    """
    Configurações do aplicativo carregadas a partir de variáveis de ambiente.
    Usa pydantic-settings para validação automática.
    """

    # API Keys
    google_maps_api_key: str = Field(default="", env="GOOGLE_MAPS_API_KEY")
    instagram_username: str = Field(default="", env="INSTAGRAM_USERNAME")
    instagram_password: str = Field(default="", env="INSTAGRAM_PASSWORD")
    mistral_api_key: str = Field(default="", env="MISTRAL_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")

    # Local LLM
    local_llm_base_url: str = Field(default="http://localhost:1234/v1", env="LOCAL_LLM_BASE_URL")
    local_llm_model: str = Field(default="mistral-7b-instruct-v0.2", env="LOCAL_LLM_MODEL")

    # Configurações AI
    default_ai_provider: str = Field(default="mistral", env="DEFAULT_AI_PROVIDER")
    default_model: str = Field(default="mistral-small-latest", env="DEFAULT_MODEL")

    # Configurações Gerais
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    scraping_delay: float = Field(default=2.0, env="SCRAPING_DELAY")
    instagram_use_session_cache: bool = Field(default=True, env="INSTAGRAM_USE_SESSION_CACHE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def _is_valid_key(self, key: str) -> bool:
        """
        Verifica se uma chave de API é válida (não vazia e não placeholder).
        
        Args:
            key: A chave a ser verificada.
            
        Returns:
            True se a chave for válida, False caso contrário.
        """
        if not key or not key.strip():
            return False
        
        placeholders = [
            "sua_chave_aqui",
            "your_key_here",
            "xxx",
            "placeholder",
            "change_me",
            "replace_me",
            "insert_key_here",
        ]
        
        return key.strip().lower() not in placeholders

    def validate_api_keys(self) -> dict:
        """
        Valida todas as chaves de API configuradas.
        
        Returns:
            Dicionário com o status de cada chave.
        """
        return {
            "google_maps": self._is_valid_key(self.google_maps_api_key),
            "instagram": bool(self.instagram_username and self.instagram_password),
            "mistral": self._is_valid_key(self.mistral_api_key),
            "openai": self._is_valid_key(self.openai_api_key),
        }

    def show_api_status(self) -> None:
        """
        Exibe o status das chaves de API formatado com Rich.
        """
        console = Console()
        status = self.validate_api_keys()
        
        table = Table(title="Status das APIs - Site Workflow v2.2")
        table.add_column("API", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Detalhes", style="yellow")

        # Google Maps
        maps_status = "✅ Configurada" if status["google_maps"] else "❌ Não configurada"
        maps_detail = "Pronta para uso" if status["google_maps"] else "Adicione GOOGLE_MAPS_API_KEY no .env"
        table.add_row("Google Maps", maps_status, maps_detail)

        # Instagram
        insta_status = "✅ Configurado" if status["instagram"] else "⚠️  Opcional"
        insta_detail = "Scraping automático habilitado" if status["instagram"] else "Coleta manual pode ser necessária"
        table.add_row("Instagram", insta_status, insta_detail)

        # Mistral
        mistral_status = "✅ Configurada" if status["mistral"] else "❌ Não configurada"
        mistral_detail = "Provedor padrão" if status["mistral"] else "Configure MISTRAL_API_KEY ou mude o provedor"
        table.add_row("Mistral AI", mistral_status, mistral_detail)

        # OpenAI
        openai_status = "✅ Configurada" if status["openai"] else "❌ Não configurada"
        openai_detail = "Alternativa disponível" if status["openai"] else "Configure OPENAI_API_KEY para usar"
        table.add_row("OpenAI", openai_status, openai_detail)

        # Local LLM
        local_status = "✅ Disponível" if self._is_valid_key(self.local_llm_base_url) else "⚠️  Verifique URL"
        local_detail = f"Modelo: {self.local_llm_model}" if self._is_valid_key(self.local_llm_base_url) else "Configure LOCAL_LLM_BASE_URL"
        table.add_row("Local LLM", local_status, local_detail)

        console.print(table)
        console.print("\n💡 Dica: Edite o arquivo .env para configurar as chaves necessárias.")

    @property
    def projects_dir(self) -> Path:
        """Diretório de projetos (cria se não existir)."""
        path = Path("projects")
        path.mkdir(exist_ok=True)
        return path

    @property
    def output_dir(self) -> Path:
        """Diretório de saída (cria se não existir)."""
        path = Path("output")
        path.mkdir(exist_ok=True)
        return path

    @property
    def templates_dir(self) -> Path:
        """Diretório de templates (cria se não existir)."""
        path = Path("templates")
        path.mkdir(exist_ok=True)
        return path

    @property
    def logs_dir(self) -> Path:
        """Diretório de logs (cria se não existir)."""
        path = Path("logs")
        path.mkdir(exist_ok=True)
        return path

    @property
    def cache_dir(self) -> Path:
        """Diretório de cache (cria se não existir)."""
        path = Path(".cache")
        path.mkdir(exist_ok=True)
        return path


# Instância global de configuração
config = Settings()
