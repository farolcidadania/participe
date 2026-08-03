import os
import re
import time
import random
import difflib
import urllib.parse
import unicodedata
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter

from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

from django.utils import timezone
from django.core.files.base import ContentFile
from django.db.models import Q

from integrations.services.discord import DiscordService
from ingest.models import MateriaSettings, MateriaHTML
from legis.models import Materia, Tramitacao, Autor
from legis.utils import MAP_REGIOES, BIBLIOTECAS_ASSUNTOS, ASSUNTOS_DIRETOS, CORRECAO_ORTOGRAFICA, ASSUNTO_PARA_TEMA_GRUPO
from camara.models import Vereador

import logging

logger = logging.getLogger(__name__)

from legis.ai.analysis import AIAnalise

BASE_URL = "https://www.cmf.sc.gov.br/tramitacoes"
AJAX_URL = "https://www.cmf.sc.gov.br/ajax/tramitacao/proposicao/" # ADD camara_id
MAX_RETRIES = 3
RETRY_BACKOFF = 2
MIN_TO_REPROCESS = 60 # minutos para o reprocessamento

# Situações que indicam encerramento definitivo da matéria no portal.
# Matérias com essas situações na última tramitação são removidas da paginação
# e devem ser desativadas no banco (desactivated=True).
SITUACOES_CONCLUSIVAS = {
    "Arquivada",
    "Tramitação Concluída",
    "Encaminhada via Ofício",
}

# Configurações de espera (em segundos)
INTERVALO_REQUISICAO = (3, 10) # Range para espera aleatória entre QUALQUER request
PAUSA_CAPTCHA = (60, 120)    # Espera longa ao detectar captcha
PLAYWRIGHT_NAV_TIMEOUT_MS = 30_000
PLAYWRIGHT_WAIT_CHALLENGE_S = 45
PLAYWRIGHT_POLL_CHALLENGE_S = 5

def _build_session() -> requests.Session:
    """Cria uma Session com retry automático para erros de rede."""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class MateriasScraper:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        ]
        self.headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session = _build_session()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._playwright_disabled_reason = None
        self.discord_service = DiscordService(username="Scraper Matérias", dev=True)
        self.created = 0
        self.new_tramitacoes = 0
        self.captchas = 0
        self.processed = 0
        
        self.arquivadas = 0
        self.concluidas = 0
        self.encaminhadas = 0
        
        self.start_time = timezone.localtime()

    def _elapsed_str(self) -> str:
        """Retorna o tempo decorrido desde self.start_time no formato HH:MM:SS."""
        total_seconds = int((timezone.localtime() - self.start_time).total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def start(self):
        try:
            # self.loopPaginacao()

            self.loopProcessamento()
        finally:
            self._close_playwright()

        duration_str = self._elapsed_str()
        lines = [
            f"Tempo : {duration_str}",
            f"Processadas: {self.processed}" if self.processed > 0 else "",
            f"Tramitações: +{self.new_tramitacoes}" if self.new_tramitacoes > 0 else "",
            f"Bloqueios: {self.captchas}" if self.captchas > 0 else "",
            f"Arquivadas: {self.arquivadas}" if self.arquivadas > 0 else "",
            f"Concluídas: {self.concluidas}" if self.concluidas > 0 else "",
            f"Encaminhadas: {self.encaminhadas}" if self.encaminhadas > 0 else "",
        ]
        msg = "\n".join(lines)
        logger.info(
            "Relatório: %s matérias processadas, %s novas tramitações em %s",
            self.processed, self.new_tramitacoes, duration_str,
        )
        self.discord_service.log_success(msg)
    
    def loopPaginacao(self):
        page = 1
        while True:
            url_pagina = f"{BASE_URL}/{page}/0/0"
            html = self.get_html_page(url_pagina, page)
            if not html:
                logger.error(f"Não foi possível obter o HTML da página {page}. Interrompendo paginação.")
                break

            next = self.process_page(html, this_page=page)

            if next:
                page += 1
            else:
                break

    def process_page(self, html, this_page):
        soup = BeautifulSoup(html, 'html.parser')

        pbw_listaprincipal = soup.find(class_="pbw_listaprincipal")
        if not pbw_listaprincipal:
            filename = f"error_page_{this_page}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            logger.warning(f"Estrutura da página {this_page} inválida (div .pbw_listaprincipal não encontrada). HTML salvo em {filename}")
            return False

        items = pbw_listaprincipal.find_all(class_="pbw_materia_conteudo")
        logger.info(f"{len(items)}itens page {this_page}")

        parsed_items = {}
        for pbw_materia_conteudo in items:
            a_tag = pbw_materia_conteudo.find("a")
            if not a_tag or not a_tag.get("href"):
                continue

            camara_id_str = a_tag["href"].split("/")[-2]
            try:
                camara_id = int(camara_id_str)
            except ValueError:
                continue

            parsed_items[camara_id] = {
                'url': a_tag["href"]
            }

        if parsed_items:
            # 1. Busca todos os settings já existentes para esses ids
            existing_settings = MateriaSettings.objects.filter(camara_id__in=parsed_items.keys())
            existing_dict = {s.camara_id: s for s in existing_settings}

            to_create = []
            to_update = []

            for camara_id, data in parsed_items.items():
                if camara_id in existing_dict:
                    obj = existing_dict[camara_id]
                    if obj.desactivated or not obj.active:
                        obj.desactivated = False
                        obj.active = True
                        to_update.append(obj)
                else:
                    to_create.append(MateriaSettings(
                        camara_id=camara_id,
                        url=data['url'],
                        desactivated=False,
                        active=True
                    ))

            # 2. Executa as inserções e atualizações em lote (bulk)
            if to_create:
                MateriaSettings.objects.bulk_create(to_create, ignore_conflicts=True)
                self.created += len(to_create)
                
            if to_update:
                MateriaSettings.objects.bulk_update(to_update, ['desactivated', 'active'])

        paginacao = soup.find(class_="pbw_paginacao")
        if not paginacao or not paginacao.strong:
            return False

        try:
            last_link = paginacao.find_all("a", href=True)[-1]
            total_pages = int(last_link["href"].rstrip("/").split("/")[-3])
        except (IndexError, ValueError):
            return False

        return this_page < total_pages

    # ------------------------------------------------------------------
    # Parte 2 – loop de processamento: percorre MateriaSettings pendentes
    # ------------------------------------------------------------------
    def loopProcessamento(self):
        threshold = timezone.localtime() - timezone.timedelta(minutes=MIN_TO_REPROCESS)
        em_tramitacao = MateriaSettings.objects.filter(
            desactivated=False,
            active=True,
        )
        pendentes = em_tramitacao.filter(
            Q(last_processed__isnull=True) | Q(last_processed__lte=threshold)
        )
        total = pendentes.count()
        if self.created > 0:
            msg = f"+{self.created} matérias em {self._elapsed_str()}, {total} pendentes"
            logger.info(msg)
            self.discord_service.log_success(msg)
        
        for settings in pendentes:
            html = self.get_html_page(settings.url, settings.camara_id)

            if html is None:
                # Se o HTML for None, pode ser captcha ou erro de rede.
                # get_html_page já cuidou da espera de captcha.
                # Não desativamos o registro para tentar novamente no futuro.
                continue

            self.process_detail(html, settings)
            logger.info(f'{self.processed}/{total} id {settings.camara_id}')

    # Mapeamento de label → código do PROPOSICAO_TIPO (busca case-insensitive)
    TIPO_MAP = {
        "emenda": "EM",
        "emenda em plenário": "EEP",
        "indicação": "IND",
        "moção": "MO",
        "projeto de decreto legislativo": "PDL",
        "projeto de lei complementar": "PDLC",
        "projeto de lei": "PDL",
        "projeto de resolução": "PDR",
        "proposta de emenda à constituição de santa catarina": "PECC",
        "proposta de emenda à lei orgânica": "PECLO",
        "recurso regimental": "RE",
        "requerimento": "REQ",
        "requerimento de informações ao executivo": "REI",
        "substitutivo global": "SG",
    }

    @staticmethod
    def _extrair_nome_sem_partido(nome_raw: str) -> str:
        """
        Recebe 'Pri Fernandes (PSD)' e retorna 'Pri Fernandes'.
        Remove qualquer sufixo entre parênteses no final.
        """
        return re.sub(r'\s*\([^)]+\)\s*$', '', nome_raw).strip()

    @staticmethod
    def _find_vereador(nome_raw: str) -> Vereador | None:
        """
        Tenta localizar um Vereador cadastrado a partir do nome vindo do scraper,
        que pode vir no formato 'Pri Fernandes (PSD)'.

        Estratégia (do mais para o menos preciso):
          1. Busca exata pelo campo nome (com ou sem partido)
          2. Busca pelo nome sem partido (iexact)
          3. Busca que começa com o nome sem partido (istartswith)
          4. Busca icontains do nome sem partido
          5. difflib.get_close_matches contra todos os nomes do banco
        """
        nome_limpo = MateriasScraper._extrair_nome_sem_partido(nome_raw)

        # 1. Exato com o texto original
        qs = Vereador.objects.filter(nome__iexact=nome_raw)
        if qs.exists():
            return qs.first()

        # 2. Exato pelo nome sem partido
        qs = Vereador.objects.filter(nome__iexact=nome_limpo)
        if qs.exists():
            return qs.first()

        # 3. nome do banco começa com o nome limpo (ex: banco tem 'Pri Fernandes (PSD)')
        qs = Vereador.objects.filter(nome__istartswith=nome_limpo)
        if qs.exists():
            return qs.first()

        # 4. Contém o nome limpo
        qs = Vereador.objects.filter(nome__icontains=nome_limpo)
        if qs.exists():
            return qs.first()

        # 5. Fallback: difflib contra todos os nomes no banco
        todos = list(Vereador.objects.values_list('id', 'nome'))
        nomes = [n for _, n in todos]
        matches = difflib.get_close_matches(nome_limpo, nomes, n=1, cutoff=0.6)
        if matches:
            match_nome = matches[0]
            vid = next(i for i, n in todos if n == match_nome)
            return Vereador.objects.get(pk=vid)

        return None

    def _resolve_tipo(self, titulo_raw: str) -> str | None:
        """
        Recebe o título completo, ex: 'PROJETO DE LEI N.º 19910/2026',
        e retorna o código do choice correspondente ou None se não reconhecido.
        Percorre o TIPO_MAP do mais específico (maior) para o menos específico.
        """
        titulo_lower = titulo_raw.lower()
        # Ordena por comprimento decrescente para priorizar matches mais longos
        for label in sorted(self.TIPO_MAP.keys(), key=len, reverse=True):
            if titulo_lower.startswith(label):
                return self.TIPO_MAP[label]
        return None

    def process_detail(self, html, settings):
        soup = BeautifulSoup(html, 'html.parser')
        pbw_listaprincipal = soup.find(class_="pbw_listaprincipal")

        if not pbw_listaprincipal:
            filename = f"error_{settings.camara_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            logger.warning(f"Div .pbw_listaprincipal não encontrada para id {settings.camara_id}. Erro salvo em {filename}")
            self.processed += 1
            return

        # Otimização: Salva apenas o conteúdo da div .pbw_listaprincipal para economizar espaço
        if settings.save_html:
            html_cortado = str(pbw_listaprincipal)
            MateriaHTML.objects.update_or_create(
                identificador_cmf=str(settings.camara_id),
                defaults={
                    'materia': settings,
                    'arquivo_html': ContentFile(html_cortado.encode('utf-8'), name=f"materia_{settings.camara_id}.html"),
                }
            )
        
        settings.last_processed = timezone.localtime()
        settings.save()

        materia = self.get_or_create_materia(settings)

        # ── Cabeçalho: data e título completo ──────────────────────────────
        linhatitulo = pbw_listaprincipal.find(class_="pbw_linhatitulo-1")
        if linhatitulo:
            divs = linhatitulo.find_all("div", recursive=False)

            # div[0] → data/hora de apresentação  (ex: "25/03/2026 17:13")
            if len(divs) >= 1:
                data_str = divs[0].get_text(strip=True)
                try:
                    materia.data_apresentacao = datetime.strptime(
                        data_str[:10], "%d/%m/%Y"
                    ).date()
                except (ValueError, IndexError):
                    pass

            # div[1] → título completo  (ex: "PROJETO DE LEI N.º 19910/2026")
            if len(divs) >= 2:
                titulo_raw = divs[1].get_text(strip=True)

                # Tipo
                tipo_code = self._resolve_tipo(titulo_raw)
                if tipo_code:
                    materia.tipo = tipo_code

                # Número e ano  (padrão: N.º NNNNN/AAAA ou Nº NNNNN/AAAA)
                m = re.search(r"[Nn]\.?\s*[º°oe]?\s*(\d+)\s*/\s*(\d{4})", titulo_raw)
                if m:
                    materia.numero = int(m.group(1))
                    materia.ano = int(m.group(2))

        # ── Corpo do documento ──────────────────────────────────────────────
        exibir = pbw_listaprincipal.find(class_="pbw_exibir_materia")
        if exibir:
            # Ementa: coletada via estilo da div (padding-left:45%)
            div_ementa = exibir.find("div", style="padding-left:45%;")
            if div_ementa:
                inner_div = div_ementa.find("div")
                if inner_div:
                    ementa = inner_div.get_text(strip=True)
                else:
                    ementa = div_ementa.get_text(strip=True)
                    
                if materia.ementa != ementa:  # corrigindo retroativo
                    materia.ementa = ementa
                    
            paragrafos = []
            for div in exibir.find_all("div", recursive=False):
                texto = div.get_text(separator="\n", strip=True)
                if texto:
                    paragrafos.append(texto)

            if paragrafos:
                materia.descricao = "\n\n".join(paragrafos)
                tools = Tools()
                materia.regiao = tools.identificar_regiao(materia.descricao)
                assunto, palavras_chave = tools.classificar_assunto(materia.get_text)
                tema = tools.ASSUNTO_PARA_TEMA.get(assunto, "")
                
                if not assunto or not tema or assunto == "Erro":
                    
                    if materia.assunto_by_ia_date and materia.assunto_by_ia and materia.assunto_by_ia != "Erro":
                        assunto = materia.assunto_by_ia
                        tema = materia.tema_by_ia
                    else:
                        texto_reduzido = f"Ementa: {materia.ementa}\nDescrição: {materia.descricao[:800]}"
                        
                        from legis.ai.analysis import AIAnalise
                        analise = AIAnalise().analise(texto_reduzido)
                        
                        assunto = analise.get("Assunto") or "Erro"
                        tema = analise.get("Tema") or "Erro"
                        
                        if assunto and assunto != "Erro":
                            materia.assunto_by_ia_date = timezone.localtime()

                # Salvar no banco os dados classificados
                materia.assunto_by_ia = assunto
                materia.tema_by_ia = tema
                materia.eixo = tools.definir_eixo(tema)
                
                desc_n = tools.normalizar(materia.descricao)
                participacao_publica = tools.definir_participacao_publica(tema)
                
                for expressao in tools.EXPRESSOES_PARTICIPACAO_PUBLICA:
                    if expressao in desc_n:
                        participacao_publica = True
                        palavras_chave = f"{palavras_chave}, {expressao}" if palavras_chave else expressao
                        
                if palavras_chave:
                    palavras_chave = tools._dedup_csv(palavras_chave)
                    palavras_chave = tools.corrigir_ortografia(palavras_chave)
                    
                materia.palavras_chaves = palavras_chave
                materia.participacao_publica = participacao_publica

        # ── Link externo (proposições) ──────────────────────────────────────
        # Botão de Facebook Share contém a URL canônica da proposição
        link_fb = pbw_listaprincipal.find(
            "a", onclick=lambda v: v and "facebook.com/sharer" in v
        )
        if link_fb:
            onclick_val = link_fb.get("onclick", "")
            m_url = re.search(r"sharer\.php\?u=([^'\"]+)", onclick_val)
            if m_url:
                materia.link_externo = urllib.parse.unquote(m_url.group(1))

        # Fallback: URL canônica da og:url no <head>
        if not materia.link_externo:
            og_url = soup.find("meta", property="og:url")
            if og_url and og_url.get("content"):
                materia.link_externo = og_url["content"]

        # ── Autores ─────────────────────────────────────────────────────────
        # Assinatura aparece em divs float:left com nome + cargo
        autores_divs = pbw_listaprincipal.find_all(
            "div",
            style=lambda s: s and "float:left" in s and "height:2cm" in s,
        )
        nomes_vistos = set()
        for div in autores_divs:
            linhas = [l.strip() for l in div.get_text("\n", strip=True).split("\n") if l.strip()]
            if linhas:
                nome_raw = linhas[0]
                if nome_raw not in nomes_vistos:
                    nomes_vistos.add(nome_raw)
                    vereador = self._find_vereador(nome_raw)
                    autor, created = Autor.objects.get_or_create(
                        nome=nome_raw,
                        defaults={'vereador': vereador}
                    )
                    if not created and autor.vereador is None and vereador is not None:
                        autor.vereador = vereador
                        autor.save()
                    
                    materia.autores.add(autor)

        # ── Protocolos da Publicação ──────────────────────────────────────────
        # Tenta encontrar o bloco de protocolos que contém a data de alteração
        protocolos_div = None
        for div in pbw_listaprincipal.find_all("div", class_="botao_avisos"):
            if "Protocolos desta Publicação" in div.get_text():
                protocolos_div = div
                break
        
        if protocolos_div:
            texto_protocolos = protocolos_div.get_text(separator=" ", strip=True)
            # Busca especificamente por "Alterado em: dd/mm/aaaa hh:mm:ss"
            m_alterado = re.search(r"Alterado em:\s*(\d{2}/\d{2}/\d{4}\s*\d{2}:\d{2}:\d{2})", texto_protocolos)
            if m_alterado:
                try:
                    dt_str = m_alterado.group(1)
                    naive_dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                    materia.camara_update = timezone.make_aware(naive_dt)
                except (ValueError, IndexError):
                    pass

        materia.save()
        self.get_tramitacoes(materia)  # pega informações de tramitação via AJAX
        self.processed += 1

    def get_or_create_materia(self, settings):
        """
        Retorna a Materia vinculada ao settings, ou cria uma nova se não existir.

        Usa try/except explícito pois `hasattr(settings, 'materia')` sempre
        retorna True para OneToOneField reverso — mesmo quando o objeto foi
        deletado — mascarando o RelatedObjectDoesNotExist.
        """
        try:
            return settings.materia
        except Materia.DoesNotExist:
            return Materia.objects.create(config=settings)

    def get_tramitacoes(self, materia):
        """
        Busca e processa as tramitações da matéria via AJAX.
            Extrai data, situação, descrição e órgão dos itens retornados no HTML.
        """
        html = self.get_html_page(AJAX_URL + str(materia.config.camara_id), materia.config.camara_id, referer=materia.config.url)
        if not html:
            return

        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all(class_='item-tramitacoes')
        
        novas = 0
        for item in items:
            # 1. Horário (formato esperado: dd/mm/aaaa hh:mm)
            horario_div = item.find(class_='item-tramitacoes__horario')
            if not horario_div:
                continue
            
            dt_str = horario_div.get_text(strip=True)
            try:
                naive_dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
                aware_dt = timezone.make_aware(naive_dt)
            except (ValueError, IndexError):
                logger.warning(f"Formato de data inválido na tramitação: {dt_str}")
                continue

            # 2. Situação (Texto em destaque na tramitação)
            passos_a = item.find(class_='item-tramitacoes__passos')
            if not passos_a:
                continue
            
            situacao_strong = passos_a.find('strong')
            if situacao_strong:
                situacao = situacao_strong.get_text(strip=True)
            else:
                situacao = passos_a.get_text(strip=True)
            
            # Limita ao tamanho do campo no banco (CharField 120)
            situacao = (situacao or "Sem Situação")[:120]

            # 3. Descrição e Órgão
            # Extraímos o restante do texto do link de passos e os detalhes extras
            descricao_partes = []
            orgao = ""
            
            # Removemos a situação e ícones para pegar apenas o comentário extra do passo
            temp_soup = BeautifulSoup(str(passos_a), 'html.parser')
            if temp_soup.strong:
                temp_soup.strong.decompose()
            for i in temp_soup.find_all('i'):
                i.decompose()
            
            passos_restante = temp_soup.get_text(separator=' ', strip=True)
            if passos_restante:
                descricao_partes.append(passos_restante)
                
            detalhes_div = item.find(class_='item-tramitacoes__detalhes')
            if detalhes_div:
                # Percorre itens detalhados (Protocolo, Sessão, Destino, etc.)
                for li in detalhes_div.find_all('li'):
                    li_text = li.get_text(separator=' ', strip=True)
                    if li_text:
                        descricao_partes.append(li_text)
                        # Se houver "Destino:", mapeamos para o campo orgao
                        if "Destino:" in li_text:
                            orgao = li_text.replace("Destino:", "").strip()
            
            descricao = " | ".join(descricao_partes)

            # 4. Salvar ou Atualizar (evita duplicatas pela data e situação exata)
            _, created = Tramitacao.objects.update_or_create(
                materia=materia,
                data=aware_dt,
                situacao=situacao,
                defaults={
                    'descricao': descricao,
                    'orgao': orgao[:120]
                }
            )
            if created:
                self.new_tramitacoes += 1
                novas += 1

        if novas > 0:
            logger.info(f"{novas} novas tramitações salvas para a matéria {materia.id}.")

        # 5. Verifica se a matéria foi concluída (última tramitação é terminal)
        ultima = materia.tramitacoes.order_by('-data').values_list('situacao', flat=True).first()
        if ultima and ultima in SITUACOES_CONCLUSIVAS:
            if ultima == "Arquivada":
                self.arquivadas += 1
            elif ultima == "Tramitação Concluída":
                self.concluidas += 1
            elif ultima == "Encaminhada via Ofício":
                self.encaminhadas += 1
            settings = materia.config
            if settings and not settings.desactivated:
                #TODO aguardando nova lógica de negocio para atualização de desativação de matérias
                settings.desactivated = True
                settings.desactivated_at = timezone.localtime()
                settings.save(update_fields=['desactivated', 'desactivated_at'])
                logger.info(
                    "Matéria %s (camara_id=%s) concluída com situação '%s' → desativada.",
                    materia.id, settings.camara_id, ultima
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _is_captcha(self, html: str) -> bool:
        """Verifica se o conteúdo do HTML aponta para um captcha ou bloqueio."""
        if not html:
            return False
        content = html.lower()
        blocked_terms = [
            "lsrecaptcha",
            "verificação de segurança",
            "verificando se você não é um robô",
            "grecaptcha.render",
            "cloudflare",
            "captcha-delivery"
        ]
        return any(p in content for p in blocked_terms)

    def _close_playwright(self):
        """Fecha o browser iniciado pelo scraper, se ele foi usado."""
        for obj in (self._context, self._browser):
            if obj:
                try:
                    obj.close()
                except Exception:
                    logger.debug("Falha ao fechar recurso Playwright.", exc_info=True)
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                logger.debug("Falha ao parar Playwright.", exc_info=True)

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)

    def _ensure_playwright_page(self):
        """Inicializa um Chromium reutilizável para atravessar o desafio do LiteSpeed."""
        if self._page:
            return self._page

        if self._playwright_disabled_reason:
            return None

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self._playwright_disabled_reason = (
                "playwright não instalado. Instale com: pip install playwright && playwright install chromium"
            )
            logger.warning(self._playwright_disabled_reason)
            return None

        try:
            # Playwright sync_api cria internamente um event loop asyncio.
            # Isso faz o Django bloquear chamadas ORM síncronas com
            # SynchronousOnlyOperation. A flag abaixo desabilita essa checagem,
            # pois nossas chamadas ORM são genuinamente síncronas.
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            self._context = self._browser.new_context(
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
                user_agent=self.headers["User-Agent"],
                extra_http_headers={
                    "Accept-Language": self.headers["Accept-Language"],
                },
            )
            self._context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                """
            )
            self._page = self._context.new_page()
            return self._page
        except Exception as exc:
            self._playwright_disabled_reason = f"Falha ao iniciar Playwright: {exc}"
            logger.warning(self._playwright_disabled_reason, exc_info=True)
            self._close_playwright()
            return None

    def _wait_playwright_challenge(self, page, url: str, ref) -> str | None:
        """Aguarda o desafio automático sair da tela e retorna o HTML liberado."""
        elapsed = 0
        logger.warning(
            "[%s] Desafio de segurança detectado em %s. Aguardando auto-resolução por até %ss.",
            ref, url, PLAYWRIGHT_WAIT_CHALLENGE_S,
        )

        while elapsed < PLAYWRIGHT_WAIT_CHALLENGE_S:
            page.wait_for_timeout(PLAYWRIGHT_POLL_CHALLENGE_S * 1000)
            elapsed += PLAYWRIGHT_POLL_CHALLENGE_S
            html = page.content()
            if not self._is_captcha(html):
                logger.info("[%s] Desafio resolvido pelo browser após %ss.", ref, elapsed)
                return html

        self.captchas += 1
        logger.warning("[%s] Bloqueio persistiu após %ss em %s.", ref, elapsed, url)
        return None

    def _get_html_page_playwright(self, url: str, ref, referer=None) -> str | None:
        page = self._ensure_playwright_page()
        if not page:
            return None

        try:
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=PLAYWRIGHT_NAV_TIMEOUT_MS,
                referer=referer or (BASE_URL if url != BASE_URL else None),
            )
            html = page.content()

            if self._is_captcha(html):
                return self._wait_playwright_challenge(page, url, ref)

            if response and response.status >= 400:
                self.discord_service.log_danger(
                    f"[{ref}] Status inesperado {response.status} em {url}"
                )
                return None

            return html
        except Exception as exc:
            logger.warning("[%s] Playwright falhou em %s: %s", ref, url, exc, exc_info=True)
            self._close_playwright()
            return None

    def get_html_page(self, url: str, ref, retry_on_captcha=True, referer=None) -> str | None:
        """Faz GET com delay aleatório e detecção de captcha."""
        html = self._get_html_page_playwright(url, ref, referer=referer)
        if html is not None:
            return html

        if (
            not self._playwright_disabled_reason
            or not self._playwright_disabled_reason.startswith("playwright não instalado")
        ):
            return None

        # Delay aleatório entre todas as requisições (detalhes, paginação, ajax)
        wait_time = random.uniform(*INTERVALO_REQUISICAO)
        time.sleep(wait_time)

        current_headers = self.headers.copy()
        if referer:
            current_headers["Referer"] = referer
        elif url != BASE_URL:
             current_headers["Referer"] = BASE_URL

        try:
            response = self.session.get(url, headers=current_headers, timeout=30)
            
            # Detecção de Captcha
            if self._is_captcha(response.text):
                logger.warning(f"[{ref}] Bloqueio de segurança (captcha) detectado em {url}")
                if retry_on_captcha:
                    pause = random.uniform(*PAUSA_CAPTCHA)
                    logger.warning(f"Aguardando {pause:.0f}s para reiniciar sessão e tentar novamente...")
                    time.sleep(pause)
                    
                    # Reinicia a sessão e troca o User-Agent
                    self.headers["User-Agent"] = random.choice(self.user_agents)
                    self.session = _build_session()
                    
                    # Tenta uma única vez após a pausa
                    return self.get_html_page(url, ref, retry_on_captcha=False, referer=referer)
                
                self.captchas += 1
                return None

            if response.status_code == 200:
                return response.text
            else:
                self.discord_service.log_danger(
                    f"[{ref}] Status inesperado {response.status_code} em {url}"
                )
                return None
        except requests.exceptions.ConnectionError as exc:
            self.discord_service.log_danger(
                f"[{ref}] Conexão falhou em {url}: {exc}"
            )
            return None
        except requests.exceptions.Timeout:
            self.discord_service.log_danger(f"[{ref}] Timeout em {url}")
            return None
        except requests.exceptions.RequestException as exc:
            self.discord_service.log_danger(f"[{ref}] Erro inesperado em {url}: {exc}")
            return None



class Tools:

    ASSUNTO_PARA_TEMA = {assunto: tema for tema, lista in ASSUNTO_PARA_TEMA_GRUPO.items() for assunto in lista}
    ASSUNTOS_VALIDOS = sorted(list(ASSUNTO_PARA_TEMA.keys()))
    EXPRESSOES_PARTICIPACAO_PUBLICA = {"tribuna livre", "reuniao ampliada", "audiencia publica"}

    
    def normalizar(self, texto):
        if not texto:
            return ""
        texto = unicodedata.normalize("NFD", texto)
        texto = texto.encode("ascii", "ignore").decode("utf-8")
        texto = texto.lower()
        texto = re.sub(r"[^a-z0-9]", " ", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto

    def identificar_regiao(self, texto):
        texto = texto.lower()
        for regiao, bairros in MAP_REGIOES.items():
            for bairro in bairros:
                if bairro in texto:
                    return regiao
        return None

    # --- FUNÇÃO PARA DEFINIR EIXO COM BASE NO TEMA---
    def definir_eixo(self, tema):
        if tema in ["Atividades Administrativas", "Criação de bloco parlamentar", "Criação de frente parlamentar"]:
            return "Manutenção e organização da atividade legislativa"
        elif tema in ["Homenagens e Títulos", "Moção", "Datas comemorativas e dias de conscientização"]:
            return "Simbólico"
        elif tema in ["Administração Pública", "Cultura, Esporte e Lazer", "Direitos dos Animais", "Direitos Humanos, Igualdade Social e Assistência Social",
                    "Educação", "Mobilidade Urbana", "Políticas de Trabalho e Renda", "Políticas de zoneamento e uso do solo",
                    "Postura, Moral e Costumes", "Saneamento", "Saúde", "Segurança Pública", "Sustentabilidade", "Zeladoria Urbana"]:
            return "Política pública"
        return ""


    # --- FUNÇÃO PARA DEFINIR PARTICIPAÇÃO PÚBLICA COM BASE NO TEMA ---
    def definir_participacao_publica(self, tema):
        if tema in ["Audiência Pública", "Consulta Pública", "Debate Público", "Audiência Pública"]:
            return True
        return False


    # --- CLASSIFICAÇÃO DE ASSUNTOS ---
    def classificar_assunto(self, descricao):
        if not descricao:
            return "", ""
        descricao_n = self.normalizar(descricao)
        palavras_chave = []

        # 1) duas camadas
        for assunto, grupos in BIBLIOTECAS_ASSUNTOS.items():
            encontrados_g1 = [v for termo in grupos["grupo1"] for v in self.gerar_variacoes_sing_plur(termo)
                            if re.search(rf"\b{re.escape(v)}\b", descricao_n)]
            encontrados_g2 = [v for termo in grupos["grupo2"] for v in self.gerar_variacoes_sing_plur(termo)
                            if re.search(rf"\b{re.escape(v)}\b", descricao_n)]
            if encontrados_g1 and encontrados_g2:
                palavras_chave = encontrados_g1 + encontrados_g2
                return assunto, self.corrigir_ortografia(self._dedup_csv(", ".join(palavras_chave)))

        # 2) camada única
        for assunto, termos in ASSUNTOS_DIRETOS.items():
            for termo in termos:
                for v in self.gerar_variacoes_sing_plur(termo):
                    if re.search(rf"\b{re.escape(v)}\b", descricao_n):
                        palavras_chave.append(v)
                        return assunto, self.corrigir_ortografia(self._dedup_csv(", ".join(palavras_chave)))

        return "", ""

    def corrigir_ortografia(self, palavras_chave):
        if not palavras_chave:
            return ""
        palavras = [p.strip() for p in palavras_chave.split(",")]
        palavras_corrigidas = []
        for palavra in palavras:
            palavra_corrigida = CORRECAO_ORTOGRAFICA.get(palavra, palavra)
            palavras_corrigidas.append(palavra_corrigida)
        return ", ".join(palavras_corrigidas)

    def _dedup_csv(self, csv_str):
        itens = [x.strip() for x in csv_str.split(",") if x.strip()]
        vistos = []
        for x in itens:
            if x not in vistos:
                vistos.append(x)
        return ", ".join(vistos)


    def gerar_variacoes_sing_plur(self, termo):
        """Gera variações sing/plur para termos simples em pt-BR."""
        variacoes = [termo]
        if termo.endswith("ao"):
            variacoes.append(termo[:-2] + "oes")
        elif termo.endswith("al"):
            variacoes.append(termo[:-2] + "ais")
        elif termo.endswith("el"):
            variacoes.append(termo[:-2] + "eis")
        elif termo.endswith("ol"):
            variacoes.append(termo[:-2] + "ois")
        elif termo.endswith("ul"):
            variacoes.append(termo[:-2] + "uis")
        elif termo.endswith(("ar", "er", "ir", "il")):
            variacoes.append(termo + "es")
        elif not termo.endswith('s'):
            variacoes.append(termo + 's')
        return list(set(variacoes))  # remove duplicatas