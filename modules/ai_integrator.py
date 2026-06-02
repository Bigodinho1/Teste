"""
Módulo de integração com IA do projeto Site Workflow v2.2.
Gerencia comunicação com Mistral, OpenAI e LLMs locais.
"""

import re
from pathlib import Path
from typing import Optional
from rich.console import Console

from openai import OpenAI
from config import config
from modules.logger import setup_logger


class AIIntegrator:
    """
    Integração com provedores de IA para geração de código e conteúdo.
    Suporta Mistral AI, OpenAI e modelos locais (LM Studio/Ollama).
    """

    def __init__(self):
        """Inicializa o cliente de IA conforme configuração."""
        self.config = config
        self.logger = setup_logger(
            __name__,
            str(config.logs_dir / "ai_integrator.log"),
            config.log_level
        )
        self.console = Console()
        
        self.client: Optional[OpenAI] = None
        self.model: str = ""
        self.provider: str = ""
        
        self._init_client()

    def _init_client(self) -> None:
        """
        Inicializa o cliente OpenAI com base no provedor configurado.
        Configura base_url apropriado para cada provedor.
        """
        provider = self.config.default_ai_provider.lower()
        self.provider = provider
        
        if provider == "mistral":
            self.model = self.config.default_model or "mistral-small-latest"
            base_url = "https://api.mistral.ai/v1"
            api_key = self.config.mistral_api_key
            
            if not self.config._is_valid_key(api_key):
                self.logger.warning("Mistral API key não configurada. Verifique o .env")
                self.console.print("[yellow]⚠️  Mistral API não configurada[/yellow]")
            
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            self.logger.info(f"Cliente Mistral AI inicializado (modelo: {self.model})")
            self.console.print(f"[green]✅ Mistral AI configurado[/green] - Modelo: {self.model}")
            
        elif provider == "openai":
            self.model = self.config.default_model or "gpt-4o"
            base_url = "https://api.openai.com/v1"
            api_key = self.config.openai_api_key
            
            if not self.config._is_valid_key(api_key):
                self.logger.warning("OpenAI API key não configurada. Verifique o .env")
                self.console.print("[yellow]⚠️  OpenAI API não configurada[/yellow]")
            
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            self.logger.info(f"Cliente OpenAI inicializado (modelo: {self.model})")
            self.console.print(f"[green]✅ OpenAI configurado[/green] - Modelo: {self.model}")
            
        elif provider == "local":
            self.model = self.config.local_llm_model
            base_url = self.config.local_llm_base_url
            api_key = "not-needed"  # LLMs locais geralmente não precisam de key
            
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            self.logger.info(f"Cliente Local LLM inicializado em {base_url} (modelo: {self.model})")
            self.console.print(f"[blue]✅ LLM Local configurado[/blue] - URL: {base_url} | Modelo: {self.model}")
            
        else:
            self.logger.error(f"Provedor desconhecido: {provider}. Usando Mistral como fallback.")
            self.provider = "mistral"
            self.model = "mistral-small-latest"
            self.client = OpenAI(
                base_url="https://api.mistral.ai/v1",
                api_key=self.config.mistral_api_key
            )

    def generate_code(self, prompt: str, output_file: str) -> bool:
        """
        Gera código HTML/CSS/JS usando a LLM configurada.
        
        Args:
            prompt: Prompt detalhado para geração do código.
            output_file: Caminho para salvar o código gerado.
            
        Returns:
            True se sucesso, False se erro.
        """
        try:
            self.logger.info(f"Gerando código com {self.provider} ({self.model})")
            self.console.print(f"\n[cyan]🤖 Gerando código com {self.provider}...[/cyan]")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um desenvolvedor web sênior especializado em criar sites institucionais modernos, responsivos e otimizados para conversão. Seu código é limpo, semântico e segue melhores práticas."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Baixa temperatura para código mais consistente
                max_tokens=8000
            )
            
            # Extrair código da resposta
            code = self._extract_code_robustly(response.choices[0].message.content)
            
            # Salvar arquivo
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code, encoding='utf-8')
            
            # Exibir uso de tokens se disponível
            if hasattr(response, 'usage') and response.usage:
                tokens_info = f"Tokens: {response.usage.prompt_tokens} input, {response.usage.completion_tokens} output"
                self.logger.info(tokens_info)
                self.console.print(f"[dim]{tokens_info}[/dim]")
            
            self.logger.info(f"Código salvo em {output_file}")
            self.console.print(f"[green]✅ Código gerado e salvo em {output_file}[/green]")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar código: {e}")
            self.console.print(f"[red]❌ Erro: {str(e)}[/red]")
            
            # Dicas para LLM local
            if self.provider == "local":
                self.console.print("\n[yellow]💡 Dicas para LLM Local:[/yellow]")
                self.console.print("  - Verifique se o servidor está rodando")
                self.console.print(f"  - Confirme a URL: {self.config.local_llm_base_url}")
                self.console.print(f"  - Modelo carregado: {self.model}")
            
            return False

    def _extract_code_robustly(self, response: str) -> str:
        """
        Extrai código HTML de forma robusta, lidando com vários formatos de resposta.
        
        CORREÇÃO: Usa regex não-gulosos para extração precisa.
        
        Args:
            response: Resposta bruta da LLM.
            
        Returns:
            Código HTML extraído.
        """
        # Estratégia 1: Procurar por ```html ... ``` com regex não-guloso
        html_block_pattern = r'```html\s*\n(.*?)```'
        match = re.search(html_block_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            code = match.group(1).strip()
            if code.startswith('<!DOCTYPE') or code.startswith('<html'):
                return code
        
        # Estratégia 2: Procurar por ``` genérico e verificar conteúdo
        generic_block_pattern = r'```\s*\n(.*?)```'
        match = re.search(generic_block_pattern, response, re.DOTALL)
        if match:
            code = match.group(1).strip()
            if code.startswith('<!DOCTYPE') or code.startswith('<html'):
                return code
        
        # Estratégia 3: Concatenar múltiplos blocos de código se necessário
        all_blocks = re.findall(r'```(?:html)?\s*\n(.*?)```', response, re.DOTALL | re.IGNORECASE)
        if all_blocks:
            combined = '\n'.join(block.strip() for block in all_blocks)
            if combined.startswith('<!DOCTYPE') or combined.startswith('<html'):
                return combined
        
        # Estratégia 4: Buscar por <!DOCTYPE ... </html> com regex não-guloso
        doctype_pattern = r'(<!DOCTYPE[^>]*>.*?</html>)'
        match = re.search(doctype_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Estratégia 5: Buscar por <html ... </html> com regex não-guloso
        html_pattern = r'(<html[^>]*>.*?</html>)'
        match = re.search(html_pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Estratégia 6: Se a resposta inteira começa com DOCTYPE ou html, usá-la
        response_stripped = response.strip()
        if response_stripped.startswith('<!DOCTYPE') or response_stripped.startswith('<html'):
            return response_stripped
        
        # Fallback: Retornar resposta bruta com aviso
        self.logger.warning("Não foi possível extrair código formatado. Retornando resposta bruta.")
        return response

    def generate_content(self, prompt: str) -> Optional[str]:
        """
        Gera conteúdo textual usando a LLM configurada.
        
        Args:
            prompt: Prompt para geração de conteúdo.
            
        Returns:
            Conteúdo gerado ou None se erro.
        """
        try:
            self.logger.info(f"Geração de conteúdo com {self.provider} ({self.model})")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um copywriter profissional especializado em sites institucionais. Seus textos são persuasivos, claros e otimizados para conversão."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Temperatura mais alta para criatividade
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            self.logger.info("Conteúdo gerado com sucesso")
            
            return content
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar conteúdo: {e}")
            return None
