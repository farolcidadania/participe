from django.contrib import admin
from .models import CamaraToken, DiscordWebhook, GoogleSheetsConfig, AIUsage, APIKeys


admin.site.register(CamaraToken)
admin.site.register(DiscordWebhook)
admin.site.register(GoogleSheetsConfig)
admin.site.register(AIUsage)
admin.site.register(APIKeys)