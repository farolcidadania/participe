from os import link
from integrations.services.camara_service import CamaraService
from camara.models import Vereador, Partido
from django.utils import timezone
from integrations.services.discord import DiscordService

class camaraController:
    def __init__(self):
        self.camara_service = CamaraService()
        self.discord_service = DiscordService(username="camaraController", dev=True)
    
    def get_vereadores(self):
        vereadores = self.camara_service.get_vereadores()
        """
        {
            "nome": "Pri Fernandes",
            "partido": "PSD",
            "funcao": "2º Vice-Presidente",
            "imagem": "https://www.cmf.sc.gov.br/news/2025/01/2025010118450717357679076304f0.jpg",
            "link": "https://www.cmf.sc.gov.br/camara/membros/show/20#pesquisa"
        },
        """
        created = 0
        removed = 0
        active_ids = []
        for vereador in vereadores:
            # "link": "https://www.cmf.sc.gov.br/camara/membros/show/20#pesquisa"
            camara_id = int(vereador["link"].split("/")[-1].split("#")[0])
            active_ids.append(camara_id)
            
            partido = Partido.objects.filter(sigla=vereador["partido"]).first()
            if not partido:
                partido = Partido.objects.create(sigla=vereador["partido"])
            
            duplicado = Vereador.objects.filter(camara_id=camara_id).first()
            if duplicado:
                changed = False
                if duplicado.nome != vereador["nome"]:
                    duplicado.nome = vereador["nome"]
                    changed = True
                if duplicado.partido != partido:
                    duplicado.partido = partido
                    changed = True
                if duplicado.funcao != vereador["funcao"]:
                    duplicado.funcao = vereador["funcao"]
                    changed = True
                if duplicado.imagem != vereador["imagem"]:
                    duplicado.imagem = vereador["imagem"]
                    changed = True
                if duplicado.link != vereador["link"]:
                    duplicado.link = vereador["link"]
                    changed = True
                if not duplicado.ativo:
                    duplicado.ativo = True
                    changed = True
                
                if changed:
                    duplicado.save()
                    self.discord_service.log_success(f"{duplicado.nome} teve seus dados atualizados.")
                continue
            
            Vereador.objects.create(
                nome=vereador["nome"],
                partido=partido,
                funcao=vereador["funcao"],
                imagem=vereador["imagem"],
                link=vereador["link"],
                camara_id=camara_id,
                ativo=True
            )
            created += 1
        
        # Desativa vereadores que não estão na lista atual
        removidos = Vereador.objects.filter(ativo=True).exclude(camara_id__in=active_ids)
        for removido in removidos:
            removido.ativo = False
            removido.data_desativacao = timezone.localdate()
            removido.save()
            self.discord_service.log_success(f"{removido.nome} fora de excercício.")
            removed += 1

        if removed > 0:
            self.discord_service.log_success (f"Foram removidos {removed} vereadores.")
        if created > 0:
            self.discord_service.log_success (f"Foram criados {created} novos vereadores.")
        return

    
    def get_proposicoes(self):
        return self.camara_service.get_proposicoes()
