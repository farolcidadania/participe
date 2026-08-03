from django.utils import timezone
from datetime import time, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from integrations.services.discord import DiscordService
from integrations.services.camara_service import CamaraService
from integrations.scraper.scraper import Scraper

import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
discord_service = DiscordService(username="Scraper Camâra")
scraper = Scraper()

class CheckTime:
    def __init__(self):
        self.last_run = None
        self.allowed_days = [0, 1, 2, 3, 4]  # seg a sex
        self.start_time = time(7, 30)
        self.end_time = time(20, 00)
        self.interval = timedelta(minutes=60)

    def now(self):
        return timezone.localtime()

    def is_valid_day(self):
        return self.now().weekday() in self.allowed_days

    def is_valid_hour(self):
        now_time = self.now().time()
        return self.start_time <= now_time <= self.end_time

    def should_run(self):
        now = self.now()

        if not self.is_valid_day():
            return False

        if not self.is_valid_hour():
            return False

        if self.last_run is None:
            self.last_run = now
            return True

        if now - self.last_run >= self.interval:
            self.last_run = now
            return True

        return False


check_time_materias = CheckTime()
check_time_vereadores = CheckTime()


def run_get_materias():
    logger.info("run_get_materias")
    if check_time_materias.should_run():
        scraper.get_materias()

def run_get_vereadores():
    logger.info("run_get_vereadores")
    if check_time_vereadores.should_run():
        try:
            camara_service = CamaraService()
            logger.info("Chamando camara_service.get_vereadores()...")
            camara_service.get_vereadores()
        except Exception as e:
            logger.error(f"[run_get_vereadores] Erro: {e}", exc_info=True)



def start_scheduler():
    if scheduler.running:
        return
        
    try:
        scheduler.add_job(
            run_get_materias,
            trigger='interval',
            minutes=60,
            id='get_materias',
            replace_existing=True,
            next_run_time=timezone.now(),
        )

        scheduler.add_job(
            run_get_vereadores,
            trigger='interval',
            minutes=60,
            id='get_vereadores',
            replace_existing=True,
            next_run_time=timezone.now(),
        )
    
        scheduler.start()
        logger.info("Scheduler iniciado!")
    except Exception as e:
        logger.info(f"Erro ao iniciar o scheduler: {e}")
