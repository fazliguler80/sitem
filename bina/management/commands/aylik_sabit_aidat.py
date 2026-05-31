from django.core.management.base import BaseCommand
from bina.models import Aidat
from datetime import datetime

class Command(BaseCommand):
    help = 'Aylık sabit aidatları oluşturur'

    def handle(self, *args, **options):
        now = datetime.now()
        result = Aidat.aylik_sabit_aidatlari_olustur(now.month, now.year)
        self.stdout.write(self.style.SUCCESS(f"{result['olusturulan']} aidat oluşturuldu, {result['guncellenen']} güncellendi."))