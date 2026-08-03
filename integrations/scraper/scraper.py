from django.utils import timezone
from integrations.scraper.materia import MateriasScraper
from integrations.services.discord import DiscordService

class Scraper:
    def __init__(self):
        self.discord_service = DiscordService(username="Scraper Camâra")

    def get_materias(self):
        scraper = MateriasScraper()
        scraper.start()
