from django.contrib import admin

from .models import MateriaSettings, MateriaHTML, ProposicaoRaw


@admin.register(MateriaSettings)
class MateriaSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "url", "active", "desactivated", "desactivated_by", "last_processed", "created_at")
    list_filter = ("active", "desactivated", "save_html")
    search_fields = ("url", "erro_messagem")
    readonly_fields = ("created_at", "last_processed", "desactivated_at")
    ordering = ("-created_at",)


@admin.register(MateriaHTML)
class MateriaHTMLAdmin(admin.ModelAdmin):
    list_display = ("id", "materia", "identificador_cmf", "processado", "created_at")
    list_filter = ("processado",)
    search_fields = ("identificador_cmf",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(ProposicaoRaw)
class ProposicaoRawAdmin(admin.ModelAdmin):
    list_display = ("api_id", "fetched_at")
    search_fields = ("api_id",)
    readonly_fields = ("fetched_at",)
    ordering = ("-fetched_at",)

