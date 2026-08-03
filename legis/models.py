from openai.types import eval_stored_completions_data_source_config
from django.db import models
from camara.models import Vereador, Comissao
from ingest.models import MateriaSettings
from django.utils import timezone
from .utils import remover_acentos

# https://www.cmf.sc.gov.br/tramitacoes
PROPOSICAO_TIPO = [
    ("EM", "Emenda"),
    ("EEP", "Emenda Em Plenário"),
    ("IND", "Indicação"),
    ("MO", "Moção"),
    ("PDL", "Projeto De Decreto Legislativo"),
    ("PDLC", "Projeto De Lei Complementar"),
    ("PDL", "Projeto De Lei"),
    ("PDR", "Projeto De Resolução"),
    ("PECC", "Proposta De Emenda à Constituição De Santa Catarina"),
    ("PECLO", "Proposta De Emenda à Lei Orgânica"),
    ("RE", "Recurso Regimental"),
    ("REQ", "Requerimento"),
    ("REI", "Requerimento De Informações Ao Executivo"),
    ("SG", "Substitutivo Global"),
]

CLASSIFICACAO_FUNCOES = {
    "Fiscalizar": {"IND", "REI", "REQ"},
    "Legislar": {"EM", "PDL", "PDLC", "PDL", "PDR", "PECC", "PECLO", "RE", "SG"},
    "Homenagear e reconhecer": {"MO"}
}
class Autor(models.Model):
    """
    Representa um autor de matéria conforme vem do scraper.
    O campo `nome` guarda o texto bruto (ex: 'Pri Fernandes (PSD)').
    O campo `vereador` vincula ao Vereador já cadastrado na câmara.
    """
    nome = models.CharField(max_length=255, unique=True)
    vereador = models.ForeignKey(
        Vereador, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='autores'
    )

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['nome']

    def __str__(self):
        if self.vereador:
            return f"{self.nome} → {self.vereador}"
        return self.nome


class Materia(models.Model):
    last_updated_sheet = models.DateTimeField(null=True, blank=True, verbose_name='Atualizado no Sheets')
    config = models.OneToOneField(MateriaSettings, related_name='materia', on_delete=models.CASCADE, null=True, blank=True)
    numero = models.IntegerField(blank=True, null=True)
    ano = models.IntegerField(blank=True, null=True)
    tipo = models.CharField(max_length=80, blank=True, null=True, choices=PROPOSICAO_TIPO)
    
    autores = models.ManyToManyField(Autor, related_name='materias')

    ementa = models.TextField(blank=True)
    descricao = models.TextField(blank=True)

    status = models.CharField(max_length=255, blank=True, null=True)
    
    eixo = models.CharField(max_length=255, blank=True, null=True)
    regiao = models.CharField(max_length=255, blank=True, null=True)
    palavras_chaves = models.TextField(blank=True, null=True)
    assunto_by_ia = models.TextField(blank=True, null=True)
    tema_by_ia = models.CharField(max_length=255, blank=True, null=True)
    assunto_by_ia_date = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='Atualizado na IA')
    data_apresentacao = models.DateField(null=True, blank=True, verbose_name='Data de Apresentação')
    participacao_publica = models.BooleanField(default=False)
    justifica_regiao = models.BooleanField(default=False)

    camara_update = models.DateTimeField(null=True, blank=True, verbose_name='Atualizado na Câmara')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    link_externo = models.URLField(null=True, blank=True)

    class Meta:
        unique_together = ['numero', 'ano', 'tipo']
        ordering = ['-ano', '-numero']

    def __str__(self):
        return f"{self.get_tipo_display} {self.get_number_p_date}"

    @property
    def get_text(self):
        return self.ementa + " " + self.descricao

    @property
    def get_function(self): # Fiscalizar / Legislar / Homenagear e reconhecer...
        for tipo_proc, func in CLASSIFICACAO_FUNCOES.items():
            if self.tipo in func:
                return tipo_proc
        return ""

    @property
    def get_regiao_display(self):
        return self.regiao or "Não se aplica"
    
    @property
    def get_internal_id(self):
        return self.config.camara_id if self.config else None

    @property
    def get_partido_materia(self):
        if self.autores:
            res = ', '.join([v.vereador.partido.nome for v in self.autores.all() if v.vereador and v.vereador.partido])
            return res
        return 'Sem partido'

    @property
    def get_number_p_date(self):
        if self.numero is None:
            return '(sem número)'
        return f"{self.numero:05d}/{self.ano}"

    @property
    def get_tipo_display(self):
        if self.tipo is None:
            return '(sem tipo)'
        return dict(PROPOSICAO_TIPO).get(self.tipo, self.tipo)

    @property
    def get_time_since_edited(self):
        if not self.camara_update:
            return '—'
        delta = timezone.now() - self.camara_update
        total_segundos = int(delta.total_seconds())
        minutos = total_segundos // 60
        horas = minutos // 60
        dias = delta.days

        if total_segundos < 60:
            return 'agora'
        elif minutos < 60:
            return f'{minutos}m'
        elif horas < 24:
            return f'{horas}h'
        elif dias < 7:
            return f'{dias}d'
        elif dias < 30:
            return f'{dias // 7}s'
        elif dias < 365:
            return f'{dias // 30}mes'
        else:
            anos = dias // 365
            meses = (dias % 365) // 30
            return f'{anos}ano - {meses}mes' if meses else f'{anos}ano'

    @property
    def get_status_display(self):
        # Se tem status no banco, usa ele
        if self.status:
            base_status = self.status
        else:
            # Caso contrário, usa a classificação dinâmica baseada no tipo e assunto
            base_status = self.classificar_status(self.get_tipo_display, self.assunto_by_ia, self.eixo)
            
        if base_status:
            if self.assunto_by_ia_date:
                return f'{base_status}|AI'
            return f'{base_status}|R'
        
        return ""


    def classificar_status(self, tipo_materia, assunto="", eixo=""):
        if not tipo_materia:
            return ""
            
        assunto = assunto or ""
        eixo = eixo or ""
            
        tipo = remover_acentos(tipo_materia).strip().lower()
        assunto = remover_acentos(assunto).strip().lower()
        eixo = remover_acentos(eixo).strip().lower()

        # Exceções
        if tipo == "requerimento" and assunto in {
            "criacao de frente parlamentar",
            "criacao de bloco parlamentar"
        }:
            return "Observada"
        if tipo == "simbolico":
            return "Mapeada"

        # Regras gerais
        if tipo in {"indicacao", "requerimento", "requerimento de informacoes ao executivo"}:
            return "Mapeada"
        if tipo == "mocao":
            return "Observada"
        if tipo in {
            "emenda", "projeto de decreto legislativo",
            "projeto de lei complementar",
            "projeto de lei", "projeto de resolucao",
            "proposta de emenda a constituicao de santa catarina",
            "proposta de emenda a lei organica",
            "recurso regimental", "substitutivo"
        }:
            return "Observada"

        print(f'Classificar status | IA: nada')
        return ""


class Tramitacao(models.Model):
    # O ForeignKey está certo: liga o "passo" ao "projeto"
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='tramitacoes')
    data = models.DateTimeField()
    situacao = models.CharField(max_length=120) # Ex: "Aguardando Parecer"
    descricao = models.TextField(blank=True)   # Ex: "Encaminhado para a Comissão de Finanças"
    orgao = models.CharField(max_length=120, blank=True) # Ex: "Comissão de Constituição e Justiça"
    criado_em = models.DateTimeField(auto_now_add=True)

    
    @property
    def get_time_since(self):
        if not self.data:
            return '—'
        delta = timezone.now() - self.data
        total_segundos = int(delta.total_seconds())
        minutos = total_segundos // 60
        horas = minutos // 60
        dias = delta.days

        if total_segundos < 60:
            return 'agora'
        elif minutos < 60:
            return f'{minutos}m atrás'
        elif horas < 24:
            return f'{horas}h atrás'
        elif dias < 7:
            return f'{dias}d atrás'
        elif dias < 30:
            semanas = dias // 7
            return f'{semanas} sem. atrás'
        elif dias < 365:
            meses = dias // 30
            return f'{meses} mes. atrás'
        else:
            anos = dias // 365
            meses = (dias % 365) // 30
            return f'{anos}a {meses}m atrás' if meses else f'{anos}a atrás'



class Autoria(models.Model):
    tramitacao = models.ForeignKey(Tramitacao, on_delete=models.CASCADE)
    autor = models.ForeignKey(Vereador, on_delete=models.CASCADE)
    principal = models.BooleanField(default=False)

    class Meta:
        unique_together = ['tramitacao', 'autor']


class Votacao(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    data = models.DateField()
    resultado = models.CharField(max_length=50)  # aprovado, rejeitado

    def total_votos(self):
        return self.voto_set.count()

    def total_favoravel(self):
        return self.voto_set.filter(voto='favoravel').count()

    def total_contrario(self):
        return self.voto_set.filter(voto='contrario').count()

    def total_abstencao(self):
        return self.voto_set.filter(voto='abstencao').count()

    def total_ausente_nao_justificado(self):
        return self.voto_set.filter(voto='ausente_nao_justificado').count()

    def total_ausente_justificado(self):
        return self.voto_set.filter(voto='ausente_justificado').count()

    def total_presente_nao_votou(self):
        return self.voto_set.filter(voto='presente_nao_votou').count()

CATALOG_VOTE = [
    ('favoravel', 'Favorável'),
    ('contrario', 'Contrário'),
    ('abstencao', 'Abstenção'),
    ('ausente_nao_justificado', 'Ausente Não Justificado'),
    ('ausente_justificado', 'Ausente Justificado'),
    ('presente_nao_votou', 'Presente Não Votou'),
]

class Voto(models.Model):
    votacao = models.ForeignKey(Votacao, on_delete=models.CASCADE)
    vereador = models.ForeignKey(Vereador, on_delete=models.CASCADE)
    voto = models.CharField(max_length=30, choices=CATALOG_VOTE)

    class Meta:
        unique_together = ['votacao', 'vereador']

class MateriaComissao(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    comissao = models.ForeignKey(Comissao, on_delete=models.CASCADE)
    data_envio = models.DateField(null=True, blank=True)


