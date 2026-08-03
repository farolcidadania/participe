from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Perfil

from integrations.services.discord import DiscordService

discord = DiscordService(username="Cadastro", dev=False)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(user=instance)
        discord.log_success(f"Novo usuário cadastrado: {instance.username}", title="Novo Usuário")
