from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from .models import camaraToken

User = get_user_model()


def get_system_user():
    """Retorna o usuário system para registro de logs."""
    user, created = User.objects.get_or_create(
        username="system",
        defaults={
            'is_active': False,
            'is_staff': False,
            'is_superuser': False,
        }
    )
    return user


@receiver(post_save, sender=camaraToken)
def log_camara_token_save(sender, instance, created, **kwargs):
    """Registra criação ou alteração de camaraToken no LogEntry."""
    system_user = get_system_user()
    
    if created:
        action_flag = ADDITION
        change_message = "Token criado"
    else:
        action_flag = CHANGE
        change_message = "Token alterado"

    LogEntry.objects.create(
        user_id=system_user.pk,
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=str(instance),
        action_flag=action_flag,
        change_message=change_message,
    )


@receiver(post_delete, sender=camaraToken)
def log_camara_token_delete(sender, instance, **kwargs):
    """Registra remoção de camaraToken no LogEntry."""
    system_user = get_system_user()

    LogEntry.objects.create(
        user_id=system_user.pk,
        content_type_id=ContentType.objects.get_for_model(instance).pk,
        object_id=instance.pk,
        object_repr=str(instance),
        action_flag=DELETION,
        change_message="Token removido",
    )
