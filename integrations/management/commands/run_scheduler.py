from django.core.management.base import BaseCommand
from integrations.scheduler import start_scheduler
import time

class Command(BaseCommand):
    help = 'Inicia o scheduler de scraping'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando scheduler...')
        start_scheduler()
        self.stdout.write('Scheduler rodando. Pressione Ctrl+C para parar.')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write('Scheduler encerrado.')
