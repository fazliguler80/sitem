from django.core.management.base import BaseCommand
from bina.models import Blok, Daire

class Command(BaseCommand):
    help = 'Otomatik olarak daireleri oluşturur'

    def handle(self, *args, **kwargs):
        # Blokları oluştur
        for blok_adi in ['A', 'B', 'C']:
            blok, created = Blok.objects.get_or_create(blok_adi=blok_adi)
            
            if blok_adi == 'A' or blok_adi == 'C':
                # A ve C blok: 16 adet 4+1, 2 adet 4+1 dublex
                for i in range(1, 17):
                    Daire.objects.get_or_create(
                        blok=blok,
                        daire_no=str(i),
                        defaults={
                            'daire_tipi': '4+1',
                            'hisse_orani': 1.00
                        }
                    )
                for i in range(17, 19):
                    Daire.objects.get_or_create(
                        blok=blok,
                        daire_no=str(i),
                        defaults={
                            'daire_tipi': 'dublex_4+1',
                            'hisse_orani': 1.25  # Dublex dairelerin hissesi daha yüksek
                        }
                    )
            
            elif blok_adi == 'B':
                # B blok: 16 adet 3+1, 2 adet 3+1 dublex
                for i in range(1, 17):
                    Daire.objects.get_or_create(
                        blok=blok,
                        daire_no=str(i),
                        defaults={
                            'daire_tipi': '3+1',
                            'hisse_orani': 0.85
                        }
                    )
                for i in range(17, 19):
                    Daire.objects.get_or_create(
                        blok=blok,
                        daire_no=str(i),
                        defaults={
                            'daire_tipi': 'dublex_3+1',
                            'hisse_orani': 1.10
                        }
                    )
        
        self.stdout.write(self.style.SUCCESS('Tüm bloklar ve daireler başarıyla oluşturuldu!'))