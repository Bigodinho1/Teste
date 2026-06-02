"""
Site Workflow v2.2 - Sistema de Criação Automática de Sites

Aplicação principal que orquestra todo o fluxo de trabalho:
1. Coleta de dados (Google Places, Instagram, concorrentes)
2. Geração da Fonte de Verdade
3. Criação de código via IA
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from config import config
from modules.scraper import WebScraper
from modules.data_processor import DataProcessor
from modules.ai_prompts import AIPromptGenerator
from modules.ai_integrator import AIIntegrator
from modules.project_manager import ProjectManager
from modules.models import BusinessData, CompetitorData, ReferenciaNacional
from modules.logger import setup_logger


class SiteWorkflow:
    """
    Classe principal que orquestra o fluxo completo de criação de sites.
    Fornece interface interativa via terminal.
    """

    def __init__(self):
        """Inicializa todos os componentes do workflow."""
        self.config = config
        self.console = Console()
        self.logger = setup_logger(
            __name__,
            str(config.logs_dir / "main.log"),
            config.log_level
        )
        
        # Inicializar módulos
        self.scraper = WebScraper()
        self.processor = DataProcessor()
        self.prompt_generator = AIPromptGenerator()
        self.ai = AIIntegrator()
        self.project_manager = ProjectManager()
        
        # Cache para último scraping (para reutilização)
        self._last_scraping_data: dict = {}

        self.console.print(Panel.fit(
            "[bold blue]Site Workflow v2.2[/bold blue]\n"
            "[dim]Automação de Criação de Sites Institucionais[/dim]",
            border_style="blue"
        ))

    def show_menu(self) -> int:
        """
        Exibe menu principal e retorna opção escolhida.
        
        Returns:
            Número da opção selecionada.
        """
        self.console.print("\n[bold]Menu Principal:[/bold]")
        self.console.print("  [cyan]1.[/cyan] Novo Projeto (Fluxo Completo)")
        self.console.print("  [cyan]2.[/cyan] Listar Projetos")
        self.console.print("  [cyan]3.[/cyan] Apenas Scraping (Fase 1)")
        self.console.print("  [cyan]4.[/cyan] Apenas Gerar Fonte de Verdade (Fase 2)")
        self.console.print("  [cyan]5.[/cyan] Apenas Gerar Código (Fase 3)")
        self.console.print("  [cyan]6.[/cyan] Sair")
        
        try:
            choice = Prompt.ask("Escolha uma opção", choices=["1", "2", "3", "4", "5", "6"])
            return int(choice)
        except (ValueError, KeyboardInterrupt):
            return 6

    def novo_projeto_fluxo_completo(self) -> None:
        """Executa fluxo completo de criação de novo projeto."""
        self.console.print("\n[bold green]🚀 Novo Projeto - Fluxo Completo[/bold green]\n")
        
        # Coletar informações do projeto
        self.console.print("[bold]Informações do Projeto:[/bold]")
        
        nome = Prompt.ask("Nome do projeto (identificador único)")
        if self.project_manager.project_exists(nome):
            self.console.print(f"[red]❌ Projeto '{nome}' já existe![/red]")
            return
        
        cliente = Prompt.ask("Nome do cliente")
        
        self.console.print("\nTipos disponíveis:")
        self.console.print("  restaurante, hotel, consultorio, loja, servicos, outro")
        tipo_negocio = Prompt.ask("Tipo de negócio", choices=[
            "restaurante", "hotel", "consultorio", "loja", "servicos", "outro"
        ])
        
        endereco_busca = Prompt.ask("Endereço para busca (ex: 'Rua X, 123 - Bairro')")
        cidade = Prompt.ask("Cidade")
        
        instagram_username = Prompt.ask("Instagram username (opcional, apenas o @)", default="")
        instagram_url = f"https://instagram.com/{instagram_username.lstrip('@')}" if instagram_username else ""
        
        facebook_url = Prompt.ask("Facebook URL (opcional)", default="")
        site_atual = Prompt.ask("Site atual (opcional)", default="")
        
        # Criar projeto
        project = self.project_manager.create_project(
            nome=nome,
            cliente=cliente,
            tipo_negocio=tipo_negocio,
            endereco_busca=endereco_busca,
            cidade=cidade,
            instagram_url=instagram_url,
            facebook_url=facebook_url,
            site_atual=site_atual
        )
        
        # Executar fases sequencialmente
        self.console.print("\n[bold]📋 Fases do Projeto:[/bold]")
        
        # Fase 1: Scraping
        if Confirm.ask("\nExecutar Fase 1 - Coleta de Dados?"):
            self.executar_scraping(nome)
        
        # Fase 2: Fonte de Verdade
        if project.scraping_concluido and Confirm.ask("\nExecutar Fase 2 - Gerar Fonte de Verdade?"):
            self.criar_fonte_verdade(nome)
        
        # Fase 3: Gerar Código
        if project.fonte_gerada and Confirm.ask("\nExecutar Fase 3 - Gerar Código com IA?"):
            self.gerar_codigo_ia(nome)
        
        self.console.print("\n[green]✅ Fluxo completo finalizado![/green]")

    def executar_scraping(self, project_name: str) -> None:
        """
        Fase 1: Executa coleta de dados.
        
        Args:
            project_name: Nome do projeto.
        """
        self.console.print(f"\n[bold cyan]🔍 Fase 1: Coleta de Dados - {project_name}[/bold cyan]\n")
        
        project = self.project_manager.get_project(project_name)
        if not project:
            return
        
        business_name = project.cliente
        location = f"{project.endereco_busca}, {project.cidade}"
        
        # Extrair username do Instagram se disponível
        instagram_username = ""
        if project.instagram_url:
            instagram_username = project.instagram_url.rstrip('/').split('/')[-1]
        
        # 1. Google Places
        self.console.print("\n[cyan]1. Buscando no Google Places...[/cyan]")
        business_data = self.scraper.search_google_places(business_name, location)
        
        if not business_data:
            self.console.print("[yellow]⚠️  Negócio não encontrado no Google Places[/yellow]")
            self.console.print("[dim]Preencha os dados manualmente depois[/dim]")
            business_data = BusinessData(nome_comercial=business_name, endereco=location)
        
        # 2. Instagram
        if instagram_username:
            self.console.print("\n[cyan]2. Coletando Instagram...[/cyan]")
            instagram_data = self.scraper.scrape_instagram(instagram_username)
            if instagram_data:
                business_data.instagram = instagram_data
                self.console.print(f"[green]✅ Instagram coletado: {instagram_data.seguidores} seguidores[/green]")
            else:
                self.console.print("[yellow]⚠️  Instagram não coletado[/yellow]")
        
        # 3. Concorrentes
        if business_data.place_id:
            self.console.print("\n[cyan]3. Buscando concorrentes próximos...[/cyan]")
            competitors = self.scraper.search_nearby_competitors(
                place_id=business_data.place_id,
                business_type=project.tipo_negocio,
                radius=5000,
                max_results=5
            )
            self.console.print(f"[green]✅ {len(competitors)} concorrentes analisados[/green]")
        else:
            competitors = []
            self.console.print("[yellow]⚠️  Sem Place ID - pulando concorrentes[/yellow]")
        
        # 4. Referências nacionais
        self.console.print("\n[cyan]4. Analisando referências nacionais...[/cyan]")
        references = self.scraper.analyze_national_references(project.tipo_negocio)
        self.console.print(f"[green]✅ {len(references)} referências analisadas[/green]")
        
        # Salvar dados brutos
        raw_data = {
            "business": business_data.model_dump(),
            "competitors": [c.model_dump() for c in competitors],
            "references": [r.model_dump() for r in references],
            "coleta_data": datetime.now().isoformat()
        }
        
        self.processor.save_raw_data(raw_data, project_name, "dados_brutos")
        
        # Atualizar projeto
        self.project_manager.update_project(
            project_name,
            business_data=business_data,
            competitors=competitors,
            referencias=references,
            scraping_concluido=True,
            fase_atual="estruturacao"
        )
        
        # Cache para reutilização
        self._last_scraping_data[project_name] = raw_data
        
        self.console.print("\n[green]✅ Fase 1 concluída![/green]")

    def criar_fonte_verdade(self, project_name: str) -> None:
        """
        Fase 2: Gera documento Fonte de Verdade.
        
        Args:
            project_name: Nome do projeto.
        """
        self.console.print(f"\n[bold cyan]📄 Fase 2: Fonte de Verdade - {project_name}[/bold cyan]\n")
        
        project = self.project_manager.get_project(project_name)
        if not project:
            return
        
        # Tentar carregar dados do projeto ou do cache
        if project.business_data:
            business_data = project.business_data
            competitors = project.competitors
            references = project.referencias
        elif project_name in self._last_scraping_data:
            data = self._last_scraping_data[project_name]
            business_data = BusinessData(**data['business'])
            competitors = [CompetitorData(**c) for c in data['competitors']]
            references = [ReferenciaNacional(**r) for r in data['references']]
        else:
            # Tentar carregar do JSON
            json_path = config.projects_dir / project_name / "dados_brutos.json"
            if json_path.exists():
                import json
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                business_data = BusinessData(**data['business'])
                competitors = [CompetitorData(**c) for c in data['competitors']]
                references = [ReferenciaNacional(**r) for r in data['references']]
            else:
                self.console.print("[red]❌ Dados de scraping não encontrados[/red]")
                self.console.print("[dim]Execute a Fase 1 primeiro[/dim]")
                return
        
        # Gerar Fonte de Verdade
        output_path = self.processor.create_source_of_truth(
            business=business_data,
            competitors=competitors,
            references=references,
            project=project
        )
        
        # Atualizar projeto
        self.project_manager.update_project(
            project_name,
            fonte_gerada=True,
            fase_atual="desenvolvimento"
        )
        
        self.console.print(f"\n[green]✅ Fonte de Verdade gerada:[/green] {output_path}")

    def gerar_codigo_ia(self, project_name: str) -> None:
        """
        Fase 3: Gera código do site usando IA.
        
        Args:
            project_name: Nome do projeto.
        """
        self.console.print(f"\n[bold cyan]🤖 Fase 3: Geração de Código - {project_name}[/bold cyan]\n")
        
        project = self.project_manager.get_project(project_name)
        if not project:
            return
        
        # Verificar se Fonte de Verdade existe
        fonte_path = config.projects_dir / project_name / "FONTE_DE_VERDADE.md"
        
        if not fonte_path.exists():
            self.console.print("[red]❌ Fonte de Verdade não encontrada[/red]")
            self.console.print("[dim]Execute a Fase 2 primeiro[/dim]")
            return
        
        # Gerar prompt
        self.console.print("[cyan]Gerando prompt para IA...[/cyan]")
        prompt = self.prompt_generator.generate_code_prompt(
            source_of_truth_path=str(fonte_path),
            framework="html"
        )
        
        # Oferecer opções
        self.console.print("\n[bold]Opções:[/bold]")
        self.console.print("  1. Gerar código agora")
        self.console.print("  2. Salvar prompt para revisão")
        self.console.print("  3. Voltar")
        
        choice = Prompt.ask("Escolha", choices=["1", "2", "3"])
        
        if choice == "1":
            # Gerar código
            output_file = config.output_dir / project_name / "site.html"
            sucesso = self.ai.generate_code(prompt, str(output_file))
            
            if sucesso:
                self.project_manager.update_project(
                    project_name,
                    codigo_gerado=True,
                    fase_atual="qa"
                )
        
        elif choice == "2":
            # Salvar prompt
            prompt_file = config.projects_dir / project_name / "prompt_ia.txt"
            prompt_file.parent.mkdir(parents=True, exist_ok=True)
            prompt_file.write_text(prompt, encoding='utf-8')
            self.console.print(f"[green]✅ Prompt salvo em {prompt_file}[/green]")

    def run(self) -> None:
        """Loop principal da aplicação."""
        try:
            while True:
                choice = self.show_menu()
                
                if choice == 1:
                    self.novo_projeto_fluxo_completo()
                elif choice == 2:
                    self.project_manager.list_projects()
                elif choice == 3:
                    project_name = Prompt.ask("Nome do projeto")
                    self.executar_scraping(project_name)
                elif choice == 4:
                    project_name = Prompt.ask("Nome do projeto")
                    self.criar_fonte_verdade(project_name)
                elif choice == 5:
                    project_name = Prompt.ask("Nome do projeto")
                    self.gerar_codigo_ia(project_name)
                elif choice == 6:
                    self.console.print("\n[bold blue]Obrigado por usar Site Workflow v2.2![/bold blue]")
                    break
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Interrompido pelo usuário[/yellow]")
        except Exception as e:
            self.logger.error(f"Erro fatal: {e}")
            self.console.print(f"[red]❌ Erro: {e}[/red]")
            sys.exit(1)


if __name__ == "__main__":
    # Mostrar status das APIs
    config.show_api_status()
    
    # Iniciar workflow
    workflow = SiteWorkflow()
    workflow.run()
