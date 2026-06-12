from django.core.management.base import BaseCommand
from bina.models import Aidat, Daire, SiteAyarlari
from datetime import date

class Command(BaseCommand):
    help = 'Tüm dairelere sabit aidat oluşturur'

    def add_arguments(self, parser):
        parser.add_argument('--ay', type=int, required=True, help='Ay (1-12)')
        parser.add_argument('--yil', type=int, default=date.today().year, help='Yıl')

    def handle(self, *args, **options):
        ay = options['ay']
        yil = options['yil']
        
        site_ayar = SiteAyarlari.objects.first()
        if not site_ayar or not site_ayar.sabit_aidat_aktif_mi:
            self.stdout.write(self.style.ERROR('Sabit aidat sistemi aktif değil!'))
            return
        
        sabit_tutar = site_ayar.sabit_aidat_miktari
        if sabit_tutar <= 0:
            self.stdout.write(self.style.ERROR(f'Sabit aidat miktarı 0: {sabit_tutar} TL'))
            return
        
        daireler = Daire.objects.filter(muaf_mi=False)
        self.stdout.write(f"Muaf olmayan daire sayısı: {daireler.count()}")
        
        olusturulan = 0
        for daire in daireler:
            aidat, created = Aidat.objects.get_or_create(
                daire=daire,
                ay=ay,
                yil=yil,
                aidat_tipi='sabit',
                defaults={
                    'tutar': sabit_tutar,
                    'aciklama': f"{ay}/{yil} Sabit Aidat - {sabit_tutar} TL",
                    'tahakkuk_tarihi': date(yil, ay, 1),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ {daire} - {sabit_tutar} TL"))
                olusturulan += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n🎉 {olusturulan} sabit aidat oluşturuldu!"))