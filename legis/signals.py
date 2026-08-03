import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Materia
from integrations.services.google_sheets import MateriasSheetService
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Materia)
def sync_materia_to_sheets(sender, instance, created, **kwargs):
    
    # if instance.last_updated_sheet:
    #     new_tramitacoes = instance.tramitacoes.filter(data__gt=instance.last_updated_sheet)
    #     if not new_tramitacoes.exists():
    #         logger.info(f"Não existem novos status para essa matéria {instance}")
    #         return
    #     logger.info(f"Identificados {new_tramitacoes}")
    
    logger.info(f"matéria atualizada {instance}")

    try:
        service = MateriasSheetService(instance)
        service.sync()
    except Exception as exc:
        logger.exception(
            "[Sheets] Erro inesperado ao sincronizar Matéria #%s com o Google Sheets: %s",
            instance.id,
            exc,
        )