import requests
import json
import logging
from datetime import date

from ..models import camaraToken
from camara.models import Vereador, Partido

logger = logging.getLogger(__name__)


class CamaraService:
    """
    doc: https://www.cmf.sc.gov.br/dadosabertos
    # https://www.cmf.sc.gov.br/jsonweb/web-aplicativo.php?keysoft={{tokendeacesso}}&call=vereadores
    """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        if not camaraToken.objects.filter(active=True).exists():
            raise Exception("camaraToken não encontrado")
        self.key = camaraToken.objects.filter(active=True).first()
        self.base_url = f"https://www.cmf.sc.gov.br/jsonweb/web-aplicativo.php?keysoft={self.key.token}&call="

    def get_vereadores(self):
        url = f"{self.base_url}vereadores"
        response = requests.get(url, headers=self.headers)
        data = response.json()

        # Salva JSON para referência
        # with open("vereadores.json", "w", encoding="utf-8") as f:
        #     json.dump(data, f, indent=4, ensure_ascii=False)

        # Sincroniza com o banco de dados
        nomes_recebidos = set()

        for item in data:
            nome = item.get("nome", "").strip()
            if not nome:
                continue

            nomes_recebidos.add(nome)

            # Busca ou cria o partido
            sigla_partido = item.get("partido", "").strip()
            partido = None
            partido, _ = Partido.objects.get_or_create(
                sigla=sigla_partido[:50],
                defaults={"nome": sigla_partido}
            )

            # Verifica se o vereador já existe
            vereador = Vereador.objects.filter(nome=nome).first()

            if vereador:
                # Atualiza dados existentes
                atualizado = False
                if vereador.partido != partido:
                    vereador.partido = partido
                    atualizado = True
                if vereador.imagem != item.get("imagem"):
                    vereador.imagem = item.get("imagem")
                    atualizado = True
                if vereador.link != item.get("link"):
                    vereador.link = item.get("link")
                    atualizado = True
                if vereador.funcao != item.get("funcao"):
                    vereador.funcao = item.get("funcao")
                    atualizado = True
                if not vereador.ativo:
                    vereador.ativo = True
                    vereador.data_desativacao = None
                    atualizado = True
                    logger.info(f"Vereador '{nome}' reativado.")

                if atualizado:
                    vereador.save()
            else:
                # Cria novo vereador
                Vereador.objects.create(
                    nome=nome,
                    partido=partido,
                    imagem=item.get("imagem"),
                    link=item.get("link"),
                    funcao=item.get("funcao"),
                    ativo=True,
                )
                logger.info(f"Novo vereador cadastrado: '{nome}' ({sigla_partido})")

        # Desativa vereadores que não estão mais na API
        vereadores_ativos = Vereador.objects.filter(ativo=True)
        for vereador in vereadores_ativos:
            if vereador.nome not in nomes_recebidos:
                vereador.ativo = False
                vereador.data_desativacao = date.today()
                vereador.save()
                logger.info(f"Vereador '{vereador.nome}' fora de exercício.")

        return data

    def get_proposicoes(self):
        url = f"{self.base_url}proposicoes"
        response = requests.get(url, headers=self.headers)
        data = response.json()
        with open("proposicoes.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return data
