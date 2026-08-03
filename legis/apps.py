from django.apps import AppConfig


class LegisConfig(AppConfig):
    name = 'legis'
    def ready(self):
        import legis.signals
