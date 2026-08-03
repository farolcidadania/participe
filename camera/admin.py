from django.contrib import admin
from .models import Vereador, Partido


@admin.register(Vereador)
class VereadorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'partido', 'ativo']
    search_fields = ['nome']
    list_filter = ['partido', 'ativo']


admin.site.register(Partido)
