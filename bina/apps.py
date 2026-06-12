# bina/apps.py
from django.apps import AppConfig

class BinaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bina'

    def ready(self):
        import bina.signals