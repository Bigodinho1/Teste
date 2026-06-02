"""
Módulo de scraping do projeto Site Workflow v2.2.
Responsável por coletar dados de Google Places, Instagram e análise de concorrentes.
"""

import time
import re
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import googlemaps
import instaloader
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import config
from modules.models import (
    BusinessData, HorarioFuncionamento, Avaliacao,
    InstagramData, InstagramPost, CompetitorData, ReferenciaNacional
)
from modules.logger import setup_logger


class WebScraper:
    """
    Classe responsável por todas as operações de scraping e coleta de dados.
    Integra Google Maps API, Instagram e análise web de concorrentes.
    """

    def __init__(self):
        """Inicializa o scraper com configurações e sessões HTTP."""
        self.config = config
        self.logger = setup_logger(
            __name__,
            str(config.logs_dir / "scraper.log"),
            config.log_level
        )
        
        # Configurar sessão HTTP com User-Agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Inicializar cliente Google Maps se chave válida
        self.gmaps = None
        if config._is_valid_key(config.google_maps_api_key):
            self.gmaps = googlemaps.Client(key=config.google_maps_api_key)
            self.logger.info("Google Maps API inicializada com sucesso")
        else:
            self.logger.warning("Google Maps API não configurada - funcionalidades limitadas")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """
        Faz uma requisição HTTP com retry automático.
        
        Args:
            url: URL para fazer a requisição.
            **kwargs: Argumentos adicionais para requests.get().
            
        Returns:
            Response da requisição.
            
        Raises:
            requests.HTTPError: Se o status code não for 200.
        """
        # Delay configurado entre requisições
        time.sleep(self.config.scraping_delay)
        
        kwargs.setdefault('timeout', self.config.request_timeout)
        response = self.session.get(url, **kwargs)
        
        if response.status_code != 200:
            raise requests.HTTPError(f"Status {response.status_code} para {url}")
        
        return response

    def _extract_whatsapp(self, phone: str) -> str:
        """
        Extrai e formata número de WhatsApp de um telefone.
        
        Args:
            phone: Número de telefone bruto.
            
        Returns:
            Número formatado apenas com dígitos, ou string vazia se inválido.
        """
        if not phone:
            return ""
        
        digits = ''.join(c for c in phone if c.isdigit())
        
        # Aceita números com 10 ou mais dígitos
        if len(digits) >= 10:
            # Prioriza formato brasileiro (11 dígitos começando com 9)
            return digits
        
        return ""

    def search_google_places(self, business_name: str, location: str) -> Optional[BusinessData]:
        """
        Busca dados de um negócio no Google Places API.
        
        Args:
            business_name: Nome do negócio para buscar.
            location: Localização para a busca (cidade, bairro, etc.).
            
        Returns:
            BusinessData com informações completas ou None se não encontrado.
        """
        if not self.gmaps:
            self.logger.error("Google Maps API não disponível")
            return None
        
        try:
            self.logger.info(f"Buscando '{business_name}' em {location}")
            
            # Buscar places
            places_result = self.gmaps.places(query=f"{business_name} {location}")
            
            if not places_result.get('results'):
                self.logger.warning(f"Nenhum resultado encontrado para {business_name}")
                return None
            
            # Pegar primeiro resultado
            place_id = places_result['results'][0]['place_id']
            
            # Obter detalhes completos
            place_details = self.gmaps.place(place_id=place_id)
            
            if place_details.get('result') is None:
                return None
            
            result = place_details['result']
            
            # Extrair horário de funcionamento
            horario = None
            if 'opening_hours' in result:
                weekday = result['opening_hours'].get('weekday_text', [])
                horario = HorarioFuncionamento(
                    segunda=weekday[0] if len(weekday) > 0 else "",
                    terca=weekday[1] if len(weekday) > 1 else "",
                    quarta=weekday[2] if len(weekday) > 2 else "",
                    quinta=weekday[3] if len(weekday) > 3 else "",
                    sexta=weekday[4] if len(weekday) > 4 else "",
                    sabado=weekday[5] if len(weekday) > 5 else "",
                    domingo=weekday[6] if len(weekday) > 6 else ""
                )
            
            # Extrair avaliações
            avaliacoes_positivas = []
            avaliacoes_negativas = []
            reviews = result.get('reviews', [])
            
            for review in reviews[:10]:  # Limitar a 10 reviews
                avaliacao = Avaliacao(
                    texto=review.get('text', ''),
                    rating=review.get('rating', 5),
                    autor=review.get('author_name'),
                    data=review.get('time')
                )
                
                if review.get('rating', 0) >= 4:
                    avaliacoes_positivas.append(avaliacao)
                elif review.get('rating', 0) <= 2:
                    avaliacoes_negativas.append(avaliacao)
            
            # Extrair telefone e WhatsApp
            telefone = result.get('formatted_phone_number', '')
            whatsapp = self._extract_whatsapp(telefone)
            
            # Coordenadas
            geometry = result.get('geometry', {})
            location_data = geometry.get('location', {})
            
            business = BusinessData(
                nome_comercial=result.get('name', ''),
                endereco=result.get('formatted_address', ''),
                telefone=telefone,
                whatsapp=whatsapp,
                horario_funcionamento=horario,
                website=result.get('website', ''),
                place_id=place_id,
                avaliacoes_positivas=avaliacoes_positivas,
                avaliacoes_negativas=avaliacoes_negativas,
                rating_medio=result.get('rating', 0.0),
                total_avaliacoes=result.get('user_ratings_total', 0),
                latitude=location_data.get('lat', 0.0),
                longitude=location_data.get('lng', 0.0)
            )
            
            self.logger.info(f"Dados coletados: {business.nome_comercial}")
            return business
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar Google Places: {e}")
            return None

    def search_nearby_competitors(
        self, 
        place_id: str, 
        business_type: str,
        radius: int = 5000,
        max_results: int = 5
    ) -> List[CompetitorData]:
        """
        Busca concorrentes próximos ao negócio principal.
        
        Args:
            place_id: Place ID do negócio principal.
            business_type: Tipo de negócio para mapear tipo do Google.
            radius: Raio de busca em metros.
            max_results: Número máximo de concorrentes para retornar.
            
        Returns:
            Lista de CompetitorData com análise dos concorrentes.
        """
        if not self.gmaps:
            self.logger.warning("Google Maps API não disponível para busca de concorrentes")
            return []
        
        try:
            # Obter localização do negócio principal
            place_details = self.gmaps.place(place_id=place_id)
            if not place_details.get('result'):
                return []
            
            location = place_details['result']['geometry']['location']
            # CORREÇÃO: Passar como dict, não tuple
            location_dict = {"lat": location['lat'], "lng": location['lng']}
            
            # Mapear tipo de negócio para tipo do Google Places
            type_mapping = {
                'restaurante': 'restaurant',
                'hotel': 'lodging',
                'consultorio': 'doctor',
                'loja': 'store',
                'servicos': 'establishment',
                'outro': 'establishment'
            }
            place_type = type_mapping.get(business_type.lower(), 'establishment')
            
            # Buscar lugares próximos
            nearby_result = self.gmaps.places_nearby(
                location=location_dict,
                radius=radius,
                type=place_type
            )
            
            competitors = []
            for place in nearby_result.get('results', [])[:max_results + 1]:
                # Pular o próprio negócio
                if place.get('place_id') == place_id:
                    continue
                
                # Tentar obter website
                competitor_data = None
                try:
                    details = self.gmaps.place(place_id=place.get('place_id'))
                    website = details.get('result', {}).get('website', '')
                    rating = details.get('result', {}).get('rating', 0.0)
                    
                    if website:
                        competitor_data = self._analyze_competitor_website({
                            'nome': place.get('name', 'Desconhecido'),
                            'website': website,
                            'rating': rating
                        })
                    else:
                        # Sem website
                        competitor_data = CompetitorData(
                            nome=place.get('name', 'Desconhecido'),
                            url_site='',
                            tem_site=False,
                            rating=rating
                        )
                except Exception as e:
                    self.logger.debug(f"Erro ao analisar concorrente {place.get('name')}: {e}")
                    continue
                
                if competitor_data:
                    competitors.append(competitor_data)
                
                if len(competitors) >= max_results:
                    break
            
            self.logger.info(f"{len(competitors)} concorrentes analisados")
            return competitors
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar concorrentes: {e}")
            return []

    def _analyze_competitor_website(self, competitor: Dict[str, Any]) -> CompetitorData:
        """
        Analisa o website de um concorrente.
        
        Args:
            competitor: Dict com nome, website e rating do concorrente.
            
        Returns:
            CompetitorData com análise completa do site.
        """
        url = competitor.get('website', '')
        if not url:
            return None
        
        # CORREÇÃO: Adicionar protocolo se ausente
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        try:
            start_time = time.time()
            response = self._make_request(url)
            load_time = time.time() - start_time
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verificar HTTPS
            tem_https = url.startswith('https://')
            
            # Verificar viewport meta tag
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            tem_viewport = viewport is not None
            
            # Buscar link de WhatsApp
            tem_whatsapp = False
            whatsapp_patterns = ['wa.me', 'whatsapp.com', 'api.whatsapp']
            for pattern in whatsapp_patterns:
                if pattern in response.text.lower():
                    tem_whatsapp = True
                    break
            
            # Análise básica de pontos fortes/fracos
            pontos_fortes = []
            pontos_fracos = []
            
            # Verificar tempo de carregamento
            if load_time < 2.0:
                pontos_fortes.append("Carregamento rápido")
            elif load_time > 5.0:
                pontos_fracos.append("Carregamento lento")
            
            # Verificar SSL
            if tem_https:
                pontos_fortes.append("Site seguro (HTTPS)")
            else:
                pontos_fracos.append("Sem certificado SSL")
            
            # Verificar mobile-friendly
            if tem_viewport:
                pontos_fortes.append("Otimizado para mobile")
            else:
                pontos_fracos.append("Não otimizado para mobile")
            
            return CompetitorData(
                nome=competitor.get('nome', 'Desconhecido'),
                url_site=url,
                tem_site=True,
                load_time=round(load_time, 2),
                tem_https=tem_https,
                tem_viewport=tem_viewport,
                tem_whatsapp=tem_whatsapp,
                pontos_fortes=pontos_fortes,
                pontos_fracos=pontos_fracos,
                rating=competitor.get('rating', 0.0)
            )
            
        except Exception as e:
            self.logger.debug(f"Erro ao analisar site {url}: {e}")
            return CompetitorData(
                nome=competitor.get('nome', 'Desconhecido'),
                url_site=url,
                tem_site=False,
                pontos_fracos=["Site indisponível ou inacessível"]
            )

    def scrape_instagram(self, username: Optional[str]) -> Optional[InstagramData]:
        """
        Coleta dados de um perfil do Instagram.
        
        Args:
            username: Nome de usuário do Instagram.
            
        Returns:
            InstagramData com perfil completo ou None se erro.
        """
        # CORREÇÃO: Verificar se username não é vazio
        if not username or username.strip() == "":
            self.logger.debug("Username do Instagram não fornecido")
            return None
        
        username = username.strip()
        
        # CORREÇÃO: Verificar credenciais antes de tentar cache
        has_credentials = (
            self.config.instagram_username and 
            self.config.instagram_password and
            self.config._is_valid_key(self.config.instagram_username)
        )
        
        try:
            self.logger.info(f"Coletando Instagram: @{username}")
            
            loader = instaloader.Instaloader(
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False
            )
            
            # Tentar carregar sessão se credenciais disponíveis
            if has_credentials and self.config.instagram_use_session_cache:
                session_file = self.config.cache_dir / f"instagram_session_{self.config.instagram_username}"
                
                try:
                    if session_file.exists():
                        loader.load_session_from_file(
                            self.config.instagram_username,
                            str(session_file)
                        )
                        self.logger.debug("Sessão do Instagram carregada do cache")
                    else:
                        loader.login(
                            self.config.instagram_username,
                            self.config.instagram_password
                        )
                        loader.save_session_to_file(str(session_file))
                        self.logger.debug("Nova sessão do Instagram criada e salva")
                except Exception as e:
                    self.logger.warning(f"Erro ao carregar/criar sessão: {e}")
            
            # Obter perfil
            profile = instaloader.Profile.from_username(loader.context, username)
            
            # Coletar posts recentes (máximo 12)
            posts_recentes = []
            try:
                for i, post in enumerate(profile.get_posts()):
                    if i >= 12:
                        break
                    
                    caption = post.caption or ""
                    posts_recentes.append(InstagramPost(
                        caption=caption[:500],  # Limitar tamanho
                        likes=post.likes,
                        comments=post.comments,
                        data=post.date.strftime("%Y-%m-%d"),
                        url=f"https://www.instagram.com/p/{post.shortcode}/"
                    ))
                    
                    # Delay entre posts
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.warning(f"Erro ao coletar posts: {e}")
            
            # Detectar linguagem (simplificado)
            linguagem = "pt-BR"  # Default para Brasil
            
            instagram_data = InstagramData(
                bio=profile.biography or "",
                website=profile.external_url or "",
                seguidores=profile.followers,
                posts_recentes=posts_recentes,
                destaques=[],  # Destaques requerem acesso adicional
                linguagem_detectada=linguagem
            )
            
            self.logger.info(f"Instagram coletado: {profile.full_name}")
            return instagram_data
            
        except instaloader.exceptions.ProfileNotExistsException:
            self.logger.warning(f"Perfil @{username} não encontrado")
            return None
        except Exception as e:
            self.logger.error(f"Erro ao coletar Instagram: {e}")
            self.logger.info("Sugestão: Tente coletar manualmente ou verifique as credenciais")
            return None

    def analyze_national_references(self, industry: str) -> List[ReferenciaNacional]:
        """
        Analisa referências nacionais do setor.
        
        Args:
            industry: Tipo de indústria/negócio.
            
        Returns:
            Lista de ReferenciaNacional com análises.
        """
        # URLs de referência por setor
        references_by_industry = {
            'restaurante': [
                'https://www.outback.com.br',
                'https://www.spoleto.com.br',
                'https://www.giraffas.com.br'
            ],
            'hotel': [
                'https://www.accor.com',
                'https://www.marriott.com',
                'https://www.hilton.com'
            ],
            'consultorio': [
                'https://www.drauziovarella.nus.org.br',
                'https://www.einstein.br'
            ],
            'loja': [
                'https://www.magazineluiza.com.br',
                'https://www.casasbahia.com.br'
            ],
            'servicos': [
                'https://www.doutora.com.br',
                'https://www.getninjas.com.br'
            ]
        }
        
        urls = references_by_industry.get(industry.lower(), [
            'https://www.rockcontent.com',
            'https://www.resultadosdigitais.com.br'
        ])
        
        referencias = []
        
        for url in urls:
            try:
                self.logger.info(f"Analisando referência: {url}")
                response = self._make_request(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Verificar hero section
                tem_hero = bool(soup.find(class_=re.compile(r'hero|banner|jumbotron', re.I)))
                
                # Verificar depoimentos
                tem_depoimentos = bool(soup.find(class_=re.compile(r'testimonial|depoimento|review', re.I)))
                
                # Contar CTAs (botões/links com texto de ação)
                cta_patterns = ['contato', 'saiba mais', 'clique aqui', 'agende', 'reserve', 'compre']
                ctas_encontrados = 0
                for link in soup.find_all(['a', 'button']):
                    text = link.get_text().lower()
                    if any(pattern in text for pattern in cta_patterns):
                        ctas_encontrados += 1
                
                # Verificar viewport
                viewport = soup.find('meta', attrs={'name': 'viewport'})
                mobile_friendly = viewport is not None
                
                # Estrutura detectada
                estrutura = []
                if soup.find('nav'):
                    estrutura.append('menu')
                if soup.find('footer'):
                    estrutura.append('rodapé')
                if tem_hero:
                    estrutura.append('hero')
                if tem_depoimentos:
                    estrutura.append('depoimentos')
                
                referencias.append(ReferenciaNacional(
                    url=url,
                    tem_hero=tem_hero,
                    tem_depoimentos=tem_depoimentos,
                    ctas_encontrados=ctas_encontrados,
                    estrutura_detectada=', '.join(estrutura),
                    mobile_friendly=mobile_friendly
                ))
                
            except Exception as e:
                self.logger.debug(f"Erro ao analisar {url}: {e}")
                continue
        
        self.logger.info(f"{len(referencias)} referências analisadas")
        return referencias
