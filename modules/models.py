"""
Modelos de dados do projeto Site Workflow v2.2.
Define as estruturas Pydantic para todos os tipos de dados utilizados.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TipoNegocio(Enum):
    """Tipos de negócio suportados pelo sistema."""
    RESTAURANTE = "restaurante"
    HOTEL = "hotel"
    CONSULTORIO = "consultorio"
    LOJA = "loja"
    SERVICOS = "servicos"
    OUTRO = "outro"


class StatusProjeto(Enum):
    """Status possíveis de um projeto."""
    DESCOBERTA = "descoberta"
    ESTRUTURACAO = "estruturacao"
    DESENVOLVIMENTO = "desenvolvimento"
    QA = "qa"
    ENTREGUE = "entregue"


class Avaliacao(BaseModel):
    """Modelo para uma avaliação de cliente."""
    texto: str
    rating: int = Field(ge=1, le=5)
    autor: Optional[str] = None
    data: Optional[str] = None


class InstagramPost(BaseModel):
    """Modelo para um post do Instagram."""
    caption: str
    likes: int
    comments: int
    data: str
    url: str


class InstagramData(BaseModel):
    """Modelo para dados completos do perfil do Instagram."""
    bio: str
    website: str
    seguidores: int
    posts_recentes: List[InstagramPost] = Field(default_factory=list)
    destaques: List[str] = Field(default_factory=list)
    linguagem_detectada: str = "pt-BR"


class HorarioFuncionamento(BaseModel):
    """Modelo para horários de funcionamento semanal."""
    segunda: str = ""
    terca: str = ""
    quarta: str = ""
    quinta: str = ""
    sexta: str = ""
    sabado: str = ""
    domingo: str = ""


class BusinessData(BaseModel):
    """
    Modelo principal para dados de negócio coletados via Google Places API.
    Inclui informações completas sobre o estabelecimento.
    """
    nome_comercial: str = ""
    endereco: str = ""
    telefone: str = ""
    whatsapp: str = ""
    horario_funcionamento: Optional[HorarioFuncionamento] = None
    website: str = ""
    place_id: str = ""
    avaliacoes_positivas: List[Avaliacao] = Field(default_factory=list)
    avaliacoes_negativas: List[Avaliacao] = Field(default_factory=list)
    rating_medio: float = 0.0
    total_avaliacoes: int = 0
    instagram: Optional[InstagramData] = None
    facebook_url: str = ""
    tripadvisor_url: str = ""
    tripadvisor_ranking: str = ""
    latitude: float = 0.0
    longitude: float = 0.0

    @field_validator('whatsapp', 'telefone', mode='before')
    @classmethod
    def clean_phone(cls, v):
        """
        Limpa números de telefone, removendo caracteres não numéricos.
        Converte None para string vazia antes de processar.
        
        Args:
            v: O valor original do telefone.
            
        Returns:
            String contendo apenas dígitos.
        """
        if v is None:
            return ""
        if not isinstance(v, str):
            v = str(v)
        return ''.join(c for c in v if c.isdigit())


class CompetitorData(BaseModel):
    """Modelo para dados de concorrentes analisados."""
    nome: str
    url_site: str
    tem_site: bool
    load_time: float = 0.0
    tem_https: bool = False
    tem_viewport: bool = False
    tem_whatsapp: bool = False
    pontos_fortes: List[str] = Field(default_factory=list)
    pontos_fracos: List[str] = Field(default_factory=list)
    rating: float = 0.0
    distancia_km: float = 0.0


class ReferenciaNacional(BaseModel):
    """Modelo para referências nacionais do setor analisadas."""
    url: str
    tem_hero: bool = False
    tem_depoimentos: bool = False
    ctas_encontrados: int = 0
    estrutura_detectada: str = ""
    mobile_friendly: bool = False


class Project(BaseModel):
    """
    Modelo principal para gerenciamento de projetos.
    Contém todas as informações sobre um projeto de criação de site.
    """
    nome: str
    cliente: str
    tipo_negocio: TipoNegocio
    data_inicio: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    status: StatusProjeto = StatusProjeto.DESCOBERTA
    fase_atual: str = "descoberta"
    
    # Flags de progresso
    scraping_concluido: bool = False
    fonte_gerada: bool = False
    codigo_gerado: bool = False
    
    # URLs e links
    instagram_url: str = ""
    facebook_url: str = ""
    site_atual: str = ""
    
    # Dados de busca
    endereco_busca: str = ""
    cidade: str = ""
    
    # Dados coletados (referências)
    business_data: Optional[BusinessData] = None
    competitors: List[CompetitorData] = Field(default_factory=list)
    referencias: List[ReferenciaNacional] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)
