"""
Módulo de gerenciamento de projetos do projeto Site Workflow v2.2.
Responsável por criar, atualizar e listar projetos.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from rich.console import Console
from rich.table import Table

from config import config
from modules.models import Project, TipoNegocio, StatusProjeto
from modules.logger import setup_logger


class ProjectManager:
    """
    Gerencia o ciclo de vida dos projetos.
    Persiste dados em JSON e fornece interface para operações CRUD.
    """

    def __init__(self):
        """Inicializa o gerenciador de projetos."""
        self.config = config
        self.logger = setup_logger(
            __name__,
            str(config.logs_dir / "project_manager.log"),
            config.log_level
        )
        self.console = Console()
        
        # Índice de projetos
        self.index_file = config.projects_dir / "projects_index.json"
        self.projects: Dict[str, Project] = {}
        
        self._load_index()

    def _load_index(self) -> None:
        """Carrega índice de projetos do arquivo JSON."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for name, project_data in data.items():
                    try:
                        project = Project(**project_data)
                        self.projects[name] = project
                    except Exception as e:
                        self.logger.warning(f"Erro ao carregar projeto {name}: {e}")
                
                self.logger.info(f"{len(self.projects)} projetos carregados")
            except Exception as e:
                self.logger.error(f"Erro ao carregar índice: {e}")
        else:
            self.logger.debug("Nenhum índice de projetos encontrado")

    def _save_index(self) -> None:
        """Salva índice de projetos no arquivo JSON."""
        try:
            data = {name: project.model_dump() for name, project in self.projects.items()}
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.debug("Índice de projetos salvo")
        except Exception as e:
            self.logger.error(f"Erro ao salvar índice: {e}")

    def create_project(
        self,
        nome: str,
        cliente: str,
        tipo_negocio: str,
        endereco_busca: str = "",
        cidade: str = "",
        instagram_url: str = "",
        facebook_url: str = "",
        site_atual: str = ""
    ) -> Project:
        """
        Cria um novo projeto.
        
        Args:
            nome: Nome do projeto (usado como identificador único).
            cliente: Nome do cliente.
            tipo_negocio: Tipo de negócio (restaurante, hotel, etc.).
            endereco_busca: Endereço para busca no Google Places.
            cidade: Cidade do negócio.
            instagram_url: URL do Instagram.
            facebook_url: URL do Facebook.
            site_atual: URL do site atual (se houver).
            
        Returns:
            Projeto criado.
        """
        # Mapear string para enum
        tipo_map = {
            'restaurante': TipoNegocio.RESTAURANTE,
            'hotel': TipoNegocio.HOTEL,
            'consultorio': TipoNegocio.CONSULTORIO,
            'loja': TipoNegocio.LOJA,
            'servicos': TipoNegocio.SERVICOS,
            'outro': TipoNegocio.OUTRO
        }
        
        tipo_enum = tipo_map.get(tipo_negocio.lower(), TipoNegocio.OUTRO)
        
        project = Project(
            nome=nome,
            cliente=cliente,
            tipo_negocio=tipo_enum,
            endereco_busca=endereco_busca,
            cidade=cidade,
            instagram_url=instagram_url,
            facebook_url=facebook_url,
            site_atual=site_atual
        )
        
        self.projects[nome] = project
        self._save_index()
        
        self.logger.info(f"Projeto '{nome}' criado")
        self.console.print(f"[green]✅ Projeto '{nome}' criado com sucesso[/green]")
        
        return project

    def update_project(self, name: str, **kwargs) -> Optional[Project]:
        """
        Atualiza atributos de um projeto existente.
        
        Args:
            name: Nome do projeto a atualizar.
            **kwargs: Atributos a atualizar.
            
        Returns:
            Projeto atualizado ou None se não encontrado.
        """
        if name not in self.projects:
            self.logger.warning(f"Projeto '{name}' não encontrado")
            return None
        
        project = self.projects[name]
        
        # Atualizar campos permitidos
        updatable_fields = [
            'status', 'fase_atual', 'scraping_concluido', 'fonte_gerada',
            'codigo_gerado', 'business_data', 'competitors', 'referencias'
        ]
        
        for key, value in kwargs.items():
            if key in updatable_fields and hasattr(project, key):
                setattr(project, key, value)
                self.logger.debug(f"Projeto '{name}': {key} atualizado")
        
        self._save_index()
        self.logger.info(f"Projeto '{name}' atualizado")
        
        return project

    def list_projects(self) -> List[Project]:
        """
        Lista todos os projetos em formato de tabela.
        
        Returns:
            Lista de projetos.
        """
        if not self.projects:
            self.console.print("[yellow]Nenhum projeto cadastrado[/yellow]")
            return []
        
        table = Table(title="Projetos - Site Workflow v2.2")
        table.add_column("Nome", style="cyan")
        table.add_column("Cliente", style="green")
        # CORREÇÃO: usar diretamente pois use_enum_values=True converte para string
        table.add_column("Tipo", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Progresso", style="blue")
        table.add_column("Início", style="dim")
        
        for project in sorted(self.projects.values(), key=lambda p: p.data_inicio, reverse=True):
            # Calcular progresso
            progress_flags = [
                project.scraping_concluido,
                project.fonte_gerada,
                project.codigo_gerado
            ]
            progress_count = sum(progress_flags)
            progress_bar = "█" * progress_count + "░" * (3 - progress_count)
            
            # CORREÇÃO: usar diretamente pois use_enum_values=True converte para string
            table.add_row(
                project.nome,
                project.cliente,
                project.tipo_negocio,  # Já é string
                project.status,  # Já é string
                progress_bar,
                project.data_inicio
            )
        
        self.console.print(table)
        return list(self.projects.values())

    def get_project(self, name: str) -> Optional[Project]:
        """
        Obtém um projeto pelo nome.
        
        Args:
            name: Nome do projeto.
            
        Returns:
            Projeto ou None se não encontrado.
        """
        project = self.projects.get(name)
        
        if not project:
            self.logger.warning(f"Projeto '{name}' não encontrado")
            self.console.print(f"[red]❌ Projeto '{name}' não encontrado[/red]")
        else:
            self.logger.debug(f"Projeto '{name}' recuperado")
        
        return project

    def delete_project(self, name: str) -> bool:
        """
        Remove um projeto.
        
        Args:
            name: Nome do projeto a remover.
            
        Returns:
            True se removido, False se não encontrado.
        """
        if name not in self.projects:
            return False
        
        del self.projects[name]
        self._save_index()
        
        self.logger.info(f"Projeto '{name}' removido")
        self.console.print(f"[green]✅ Projeto '{name}' removido[/green]")
        
        return True

    def project_exists(self, name: str) -> bool:
        """
        Verifica se um projeto existe.
        
        Args:
            name: Nome do projeto.
            
        Returns:
            True se existe, False caso contrário.
        """
        return name in self.projects
