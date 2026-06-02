"""
Módulo de geração de prompts para IA do projeto Site Workflow v2.2.
Cria prompts otimizados para geração de código e conteúdo via LLMs.
"""

from pathlib import Path
from typing import Optional


class AIPromptGenerator:
    """
    Gera prompts estruturados para IAs generativas.
    Otimizado para Mistral, OpenAI e modelos locais.
    """

    def generate_code_prompt(
        self,
        source_of_truth_path: str,
        framework: str = "html"
    ) -> str:
        """
        Gera prompt detalhado para geração de código do site.
        
        Args:
            source_of_truth_path: Caminho para o arquivo Fonte de Verdade.
            framework: Framework target ('html' ou 'react').
            
        Returns:
            Prompt completo para a LLM.
        """
        # Ler conteúdo da Fonte de Verdade
        source_path = Path(source_of_truth_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Fonte de Verdade não encontrada: {source_path}")
        
        source_content = source_path.read_text(encoding='utf-8')
        
        # Definir configurações por framework
        if framework.lower() == "react":
            framework_specs = """
- Framework: React 18+ com functional components e hooks
- Estilização: CSS Modules ou Tailwind CSS
- Estrutura: Componentes modulares (Header, Hero, About, Services, Testimonials, Contact, Footer)
- Responsividade: Mobile-first com breakpoints padrão
- Acessibilidade: ARIA labels, navegação por teclado
"""
            delivery_format = "Código React completo com todos os componentes em arquivos separados"
        else:
            framework_specs = """
- Framework: HTML5 semântico + CSS3 + JavaScript vanilla
- Estilização: CSS inline no <style> para entrega única
- Estrutura: Single Page Application com seções âncora
- Responsividade: Media queries para mobile, tablet e desktop
- Acessibilidade: Tags semânticas, alt em imagens, contraste adequado
"""
            delivery_format = "HTML completo em um único arquivo com CSS e JS inline"
        
        prompt = f"""# Tarefa: Criar Site Institucional de Página Única

## 📋 Contexto do Projeto

Você é um desenvolvedor web sênior especializado em criar sites institucionais modernos e responsivos.
Sua tarefa é gerar o código completo de um site baseado nas informações abaixo.

## 🎯 Regras Anti-Alucinação (CRÍTICO)

1. **NÃO invente informações** - Use APENAS os dados fornecidos na Fonte de Verdade
2. **NÃO crie textos genéricos** - Se não houver informação específica, use placeholders claros como [INSERIR TEXTO]
3. **NÃO alucine URLs** - Links devem ser # para âncoras internas ou vazios se não especificado
4. **NÃO invente depoimentos** - Use apenas os depoimentos reais fornecidos
5. **Mantenha fidelidade** - Respeite nome comercial, endereço, telefones exatamente como estão

## 📄 Fonte de Verdade

{source_content}

## 🔧 Especificações Técnicas

{framework_specs}

### Requisitos Obrigatórios

1. **Performance**
   - Load time inicial < 3 segundos
   - Imagens otimizadas (use placeholders se não tiver URLs)
   - CSS/JS minificados quando possível

2. **SEO**
   - Meta tags completas (title, description, keywords, og:tags)
   - Schema.org JSON-LD para negócio local
   - URLs amigáveis para âncoras

3. **Conversão**
   - Botão WhatsApp flutuante em todas as páginas
   - CTAs claros e visíveis
   - Formulário de contato funcional (pode usar formspree ou similar)

## 🎨 Estrutura Visual Requerida

O site DEVE conter as seguintes seções nesta ordem:

1. **Header/Navegação**
   - Logo (placeholder se não tiver)
   - Menu com links âncora
   - Botão CTA principal

2. **Hero Section**
   - Título impactante baseado no negócio
   - Subtítulo com proposta de valor
   - CTA primário (WhatsApp ou Agendamento)
   - Imagem de fundo ou cor sólida

3. **Sobre Nós**
   - História do negócio
   - Diferenciais competitivos
   - Fotos/equipe (placeholders)

4. **Produtos/Serviços**
   - Cards ou lista com descrição
   - Preços (se disponíveis na Fonte de Verdade)
   - CTAs individuais

5. **Depoimentos**
   - Usar APENAS avaliações reais da Fonte de Verdade
   - Formato: cards com estrelas, texto e autor
   - Mínimo 3, máximo 6 depoimentos

6. **Localização/Contato**
   - Endereço completo
   - Mapa incorporado (Google Maps iframe - placeholder se não tiver API key)
   - Telefone, WhatsApp, email
   - Horário de funcionamento

7. **Rodapé**
   - Links rápidos
   - Redes sociais (se disponíveis)
   - Copyright e informações legais

## 🎨 Paleta de Cores Sugerida

Baseado no tipo de negócio, sugira uma paleta profissional:

- **Cor Primária:** A ser definida (sugira baseada no setor)
- **Cor Secundária:** Complementar
- **Cor de Destaque:** Para CTAs (contraste alto)
- **Fundo:** Claro para legibilidade
- **Texto:** Escuro (#333 ou similar)

## 📦 Entrega Esperada

{delivery_format}

O código deve:
- Ser completamente funcional ao copiar/colar
- Não depender de build steps ou ferramentas externas
- Incluir comentários explicativos nas seções principais
- Ter tratamento básico de erros em formulários

## ⚠️ Validação Final

Antes de finalizar, verifique:
- [ ] Todas as informações batem com a Fonte de Verdade
- [ ] Não há dados inventados ou alucinados
- [ ] O site é totalmente responsivo
- [ ] Todos os CTAs estão funcionais
- [ ] O código é semanticamente correto

---

Gere agora o código completo seguindo todas as especificações acima.
"""
        
        return prompt

    def generate_content_prompt(
        self,
        business_type: str,
        tone: str = "profissional",
        source_of_truth: Optional[str] = None
    ) -> str:
        """
        Gera prompt para criação de conteúdo textual (copywriting).
        
        Args:
            business_type: Tipo de negócio.
            tone: Tom de voz desejado (profissional, descontraído, luxuoso, etc.).
            source_of_truth: Conteúdo da Fonte de Verdade (opcional).
            
        Returns:
            Prompt para geração de conteúdo.
        """
        source_context = f"\n\n## Informações do Negócio\n\n{source_of_truth}" if source_of_truth else ""
        
        prompt = f"""# Tarefa: Criar Copy para Site Institucional

## Contexto

Você é um copywriter profissional especializado em sites institucionais.
Sua tarefa é criar textos persuasivos e envolventes para um site.

## Tipo de Negócio

{business_type}

## Tom de Voz

{tone}

- Use linguagem adequada ao público-alvo
- Seja claro e direto
- Inclua calls-to-action persuasivos
- Evite jargões excessivos{source_context}

## Entregáveis

Gere um JSON com a seguinte estrutura:

```json
{{
    "hero": {{
        "titulo": "Título principal impactante",
        "subtitulo": "Subtítulo complementar",
        "cta_principal": "Texto do botão principal"
    }},
    "sobre": {{
        "titulo": "Título da seção sobre",
        "texto": "Parágrafo sobre a história e diferenciais"
    }},
    "servicos": [
        {{
            "nome": "Nome do serviço 1",
            "descricao": "Descrição curta",
            "cta": "Texto do botão"
        }}
    ],
    "depoimentos_cta": "Chamada para seção de depoimentos",
    "contato_cta": "Chamada final para ação",
    "whatsapp_message": "Mensagem padrão para clique no WhatsApp"
}}
```

## Regras

1. Mantenha títulos com máximo de 60 caracteres
2. Subtítulos com máximo de 120 caracteres
3. Textos descritivos com 2-4 frases curtas
4. CTAs com verbos de ação imperativos
5. Adapte ao tom de voz especificado

Gere o JSON agora.
"""
        
        return prompt
