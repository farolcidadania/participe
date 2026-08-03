from django.contrib import admin
from .models import (
    Materia, Tramitacao, Autor, Autoria,
    Votacao, Voto, MateriaComissao
)


class TramitacaoInline(admin.TabularInline):
    model = Tramitacao
    extra = 0
    readonly_fields = ('data', 'situacao', 'descricao', 'orgao', 'criado_em')
    ordering = ['-data']
    can_delete = False


class MateriaComissaoInline(admin.TabularInline):
    model = MateriaComissao
    extra = 0


class VotoInline(admin.TabularInline):
    model = Voto
    extra = 0
    readonly_fields = ('vereador', 'voto')
    can_delete = False


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'numero', 'ano', 'eixo', 'regiao', 'participacao_publica', 'tem_tramitacoes', 'formated_data_apresentacao', 'formated_atualizado_em')
    list_filter = ('tipo', 'ano', 'eixo', 'regiao', 'participacao_publica', 'data_apresentacao')
    search_fields = ('numero', 'ementa', 'descricao')
    readonly_fields = ('criado_em', 'atualizado_em', 'assunto_by_ia_date')
    ordering = ['-ano', '-numero']
    date_hierarchy = 'data_apresentacao'
    inlines = [TramitacaoInline, MateriaComissaoInline]
    filter_horizontal = ('autores',)

    fieldsets = (
        ('Identificação', {
            'fields': ('config', 'tipo', 'numero', 'ano', 'autores', 'data_apresentacao', 'link_externo')
        }),
        ('Conteúdo', {
            'fields': ('ementa', 'descricao')
        }),
        ('Classificação', {
            'fields': (('status', 'eixo', 'regiao'), 'palavras_chaves', ('participacao_publica', 'justifica_regiao'))
        }),
        ('Inteligência Artificial', {
            'fields': ('assunto_by_ia', 'tema_by_ia')
        }),
        ('Auditoria', {
            'fields': ('camara_update', 'criado_em', 'atualizado_em', 'assunto_by_ia_date'),
            'classes': ('collapse',)
        }),
    )

    def formated_data_apresentacao(self, obj):
        return obj.data_apresentacao.strftime('%d/%m/%Y')
    formated_data_apresentacao.short_description = 'Apresentado'

    def formated_atualizado_em(self, obj):
        return obj.get_time_since_edited
    formated_atualizado_em.short_description = 'Editado'

    @admin.display(description='Tramitações', boolean=False)
    def tem_tramitacoes(self, obj):
        count = obj.tramitacoes.count()
        return count if count > 0 else '—'


@admin.register(Tramitacao)
class TramitacaoAdmin(admin.ModelAdmin):
    list_display = ('materia', 'situacao', 'orgao', 'data', 'criado_em')
    list_filter = ('situacao', 'orgao', 'data')
    search_fields = ('materia__numero', 'situacao', 'descricao', 'orgao')
    date_hierarchy = 'data'
    ordering = ['-data']
    raw_id_fields = ('materia',)


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'vereador')
    search_fields = ('nome', 'vereador__nome')
    list_filter = ('vereador',)
    raw_id_fields = ('vereador',)


@admin.register(Votacao)
class VotacaoAdmin(admin.ModelAdmin):
    list_display = ('materia', 'data', 'resultado', 'total_votos', 'total_favoravel', 'total_contrario', 'total_abstencao')
    list_filter = ('resultado', 'data')
    search_fields = ('materia__numero',)
    date_hierarchy = 'data'
    ordering = ['-data']
    inlines = [VotoInline]


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = ('votacao', 'vereador', 'voto')
    list_filter = ('voto',)
    search_fields = ('vereador__nome',)
    raw_id_fields = ('votacao', 'vereador')


@admin.register(MateriaComissao)
class MateriaComissaoAdmin(admin.ModelAdmin):
    list_display = ('materia', 'comissao', 'data_envio')
    list_filter = ('comissao',)
    search_fields = ('materia__numero',)
    raw_id_fields = ('materia', 'comissao')
