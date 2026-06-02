"""
Módulo de processamento de dados do projeto Site Workflow v2.2.
Responsável por gerar documentos e salvar dados coletados.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Template

from config import config
from modules.models import BusinessData, CompetitorData, ReferenciaNacional, Project


class DataProcessor:
    """
    Processa dados coletados e gera documentação estruturada.
    Cria o documento "Fonte de Verdade" em Markdown.
    """

    def create_source_of_truth(
        self,
        business: BusinessData,
        competitors: List[CompetitorData],
        references: List[ReferenciaNacional],
        project: Project
    ) -> str:
        """
        Gera o documento "Fonte de Verdade" em Markdown usando template Jinja2.
        
        Args:
            business: Dados principais do negócio.
            competitors: Lista de concorrentes analisados.
            references: Lista de referências nacionais.
            project: Informações do projeto.
            
        Returns:
            Caminho para o arquivo Markdown gerado.
        """
        # Template Jinja2 embutido para Fonte de Verdade
        template_str = """# Fonte de Verdade - {{ project.nome }}

## 📋 Dados Cadastrais

**Nome Comercial:** {{ business.nome_comercial }}
**Endereço:** {{ business.endereco }}
**Telefone:** {{ business.telefone }}
**WhatsApp:** {{ business.whatsapp }}
**Website Atual:** {{ business.website if business.website else 'Não informado' }}
**Rating Médio:** {{ business.rating_medio }} ({{ business.total_avaliacoes }} avaliações)

{% if business.horario_funcionamento %}
### Horário de Funcionamento
- **Segunda:** {{ business.horario_funcionamento.segunda }}
- **Terça:** {{ business.horario_funcionamento.terca }}
- **Quarta:** {{ business.horario_funcionamento.quarta }}
- **Quinta:** {{ business.horario_funcionamento.quinta }}
- **Sexta:** {{ business.horario_funcionamento.sexta }}
- **Sábado:** {{ business.horario_funcionamento.sabado }}
- **Domingo:** {{ business.horario_funcionamento.domingo }}
{% endif %}

## 🌐 Presença Digital

{% if business.instagram %}
### Instagram
- **Bio:** {{ business.instagram.bio }}
- **Seguidores:** {{ business.instagram.seguidores }}
- **Website na Bio:** {{ business.instagram.website }}
- **Posts Recentes:** {{ business.instagram.posts_recentes|length }} posts analisados
{% endif %}

{% if business.facebook_url %}
### Facebook
- **URL:** {{ business.facebook_url }}
{% endif %}

## ⭐ Diferenciais de Depoimentos

### Avaliações Positivas Destacadas
{% for avaliacao in business.avaliacoes_positivas[:5] %}
- **{{ avaliacao.autor or 'Anônimo' }}** ({{ avaliacao.rating }}⭐): {{ avaliacao.texto[:100] }}...
{% endfor %}

### Pontos de Atenção (Avaliações Negativas)
{% for avaliacao in business.avaliacoes_negativas[:3] %}
- **{{ avaliacao.autor or 'Anônimo' }}** ({{ avaliacao.rating }}⭐): {{ avaliacao.texto[:100] }}...
{% endfor %}

## 🏆 Análise Competitiva

{% for competitor in competitors %}
### {{ competitor.nome }}
- **Site:** {{ competitor.url_site if competitor.tem_site else 'Não possui' }}
- **Tempo de Carregamento:** {{ competitor.load_time }}s
- **HTTPS:** {{ '✅' if competitor.tem_https else '❌' }}
- **Mobile-Friendly:** {{ '✅' if competitor.tem_viewport else '❌' }}
- **WhatsApp:** {{ '✅' if competitor.tem_whatsapp else '❌' }}
- **Pontos Fortes:** {{ competitor.pontos_fortes|join(', ') if competitor.pontos_fortes else 'N/A' }}
- **Pontos Fracos:** {{ competitor.pontos_fracos|join(', ') if competitor.pontos_fracos else 'N/A' }}

{% endfor %}

## 📊 Padrões de Mercado (Referências Nacionais)

{% for ref in references %}
### {{ ref.url }}
- **Hero Section:** {{ '✅' if ref.tem_hero else '❌' }}
- **Depoimentos:** {{ '✅' if ref.tem_depoimentos else '❌' }}
- **CTAs Encontrados:** {{ ref.ctas_encontrados }}
- **Mobile-Friendly:** {{ '✅' if ref.mobile_friendly else '❌' }}
- **Estrutura:** {{ ref.estrutura_detectada }}

{% endfor %}

## 🏗️ Estrutura Recomendada do Site

Baseado na análise competitiva e referências de mercado, recomenda-se:

### Seções Obrigatórias
1. **Hero Section** - Banner principal com proposta de valor clara
2. **Sobre Nós** - História e diferenciais do negócio
3. **Produtos/Serviços** - Catálogo ou lista de serviços
4. **Depoimentos** - Prova social com avaliações reais
5. **Localização** - Mapa e informações de contato
6. **Rodapé** - Links rápidos e informações legais

### Calls-to-Action (CTAs) Prioritários
- Botão WhatsApp flutuante
- "Agende sua visita" / "Faça seu pedido"
- "Saiba mais" em produtos/serviços
- Link para redes sociais

## 🔧 Diretrizes Técnicas

- **Framework:** HTML5 + CSS3 + JavaScript vanilla
- **Responsividade:** Mobile-first obrigatório
- **Performance:** Load time < 3 segundos
- **SEO:** Meta tags, schema.org, URLs amigáveis
- **Acessibilidade:** WCAG 2.1 nível AA

## ✅ Checklist de Aprovação

- [ ] Cliente aprovou estrutura proposta
- [ ] Conteúdo textual revisado
- [ ] Imagens otimizadas (< 200KB cada)
- [ ] Links de contato testados
- [ ] Site testado em mobile e desktop
- [ ] Google Analytics instalado
- [ ] SSL configurado

## 📝 Observações

{% if project.instagram_url %}
- Perfil do Instagram: {{ project.instagram_url }}
{% endif %}
{% if project.facebook_url %}
- Página do Facebook: {{ project.facebook_url }}
{% endif %}

---

*Documento gerado automaticamente por Site Workflow v2.2 em {{ data_geracao }}*
"""

        template = Template(template_str)
        
        # Renderizar template com dados
        content = template.render(
            project=project.model_dump(),
            business=business.model_dump(),
            competitors=[c.model_dump() for c in competitors],
            references=[r.model_dump() for r in references],
            data_geracao=Path.now().strftime("%d/%m/%Y %H:%M") if hasattr(Path, 'now') else ""
        )
        
        # Criar diretório do projeto se não existir
        project_dir = config.projects_dir / project.nome
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar arquivo
        output_path = project_dir / "FONTE_DE_VERDADE.md"
        output_path.write_text(content, encoding='utf-8')
        
        return str(output_path)

    def save_raw_data(
        self,
        data: Dict[str, Any],
        project_name: str,
        filename: str
    ) -> str:
        """
        Salva dados brutos em formato JSON no diretório do projeto.
        
        Args:
            data: Dicionário com os dados a serem salvos.
            project_name: Nome do projeto (cria diretório).
            filename: Nome do arquivo (sem extensão).
            
        Returns:
            Caminho para o arquivo JSON salvo.
        """
        # Criar diretório do projeto
        project_dir = config.projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Salvar JSON
        output_path = project_dir / f"{filename}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(output_path)
