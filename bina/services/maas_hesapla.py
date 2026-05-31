from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from ..models import Personel, AsgariUcret, MaasBordrosu

class MaasHesaplayici:
    """SGK kriterlerine uygun maaş hesaplayıcı"""
    
    def __init__(self, yil):
        self.yil = yil
        self.asgari = AsgariUcret.objects.get(yil=yil)
        self.saatlik_ucret = self.asgari.brut_ucret / Decimal(225)
        self.gunluk_ucret = self.asgari.brut_ucret / Decimal(30)
    
    # ==================== NETTEN BRÜTE HESAPLAMA ====================
    
    def netten_brute(self, net_maas):
        """Net maaştan brüt maaş hesapla (hassas)"""
        from decimal import Decimal, ROUND_HALF_UP
        
        net_maas = Decimal(str(net_maas))
        asgari_brut = self.asgari.brut_ucret
        asgari_net = Decimal('28075.50')
        
        # Asgari ücretten düşükse asgari brütü döndür
        if net_maas <= asgari_net:
            return asgari_brut
        
        # İlk tahmin
        fark = net_maas - asgari_net
        tahmin = asgari_brut + (fark * Decimal('1.3'))  # Katsayı 1.25'ten 1.3'e çıkarıldı
        
        # Hassas iterasyon
        for _ in range(20):
            sgk = tahmin * Decimal('0.14')
            issizlik = tahmin * Decimal('0.01')
            
            if tahmin <= asgari_brut:
                gelir_vergisi = Decimal('0')
                damga_vergisi = Decimal('0')
            else:
                asgari_ustu = tahmin - asgari_brut
                asgari_ustu_sgk = asgari_ustu * Decimal('0.14')
                asgari_ustu_issizlik = asgari_ustu * Decimal('0.01')
                vergi_matrah = asgari_ustu - asgari_ustu_sgk - asgari_ustu_issizlik
                gelir_vergisi = vergi_matrah * Decimal('0.15')
                damga_vergisi = asgari_ustu * Decimal('0.00759')
            
            toplam_kesinti = sgk + issizlik + gelir_vergisi + damga_vergisi
            hesaplanan_net = tahmin - toplam_kesinti
            
            if abs(hesaplanan_net - net_maas) < Decimal('0.10'):
                return tahmin.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Düzeltme
            fark = net_maas - hesaplanan_net
            tahmin = tahmin + fark
        
        return tahmin.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # ==================== EK ÖDEMELER ====================
    
    def fazla_mesai_hesapla(self, saat):
        return self.saatlik_ucret * Decimal(1.5) * Decimal(str(saat))
    
    def resmi_tatil_hesapla(self, gun):
        return self.gunluk_ucret * Decimal(2) * Decimal(str(gun))
    
    def bayram_hesapla(self, gun):
        return self.gunluk_ucret * Decimal(2.5) * Decimal(str(gun))
    
    # ==================== KESİNTİ HESAPLAMA ====================
    
    def hesapla_kesintiler(self, brut_maas, personel=None):
        """
        Brüt maaş üzerinden SGK, işsizlik, gelir vergisi ve damga vergisi hesaplar.
        Asgari ücret gelir vergisi ve damga vergisinden muaftır.
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        brut_maas = Decimal(str(brut_maas))
        asgari_brut = self.asgari.brut_ucret
        
        # 1. SGK İşçi Payı (tüm brüt üzerinden)
        sgk_orani = Decimal('0.14')
        if personel and personel.sgk_tipi == 'engelli':
            sgk_orani = Decimal('0.12')
        elif personel and personel.sgk_tipi == 'yuzde40':
            sgk_orani = Decimal('0.084')
        
        sgk = (brut_maas * sgk_orani).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # 2. İşsizlik İşçi Payı (tüm brüt üzerinden)
        issizlik = (brut_maas * Decimal('0.01')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # 3. Gelir Vergisi ve Damga Vergisi (SADECE ASGARİ ÜSTÜNE)
        if brut_maas <= asgari_brut:
            gelir_vergisi = Decimal('0')
            damga_vergisi = Decimal('0')
        else:
            # Asgari üstü kısım
            asgari_ustu = brut_maas - asgari_brut
            
            # Asgari üstü kısmın SGK ve işsizliği
            asgari_ustu_sgk = (asgari_ustu * sgk_orani).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            asgari_ustu_issizlik = (asgari_ustu * Decimal('0.01')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Vergi matrahı (asgari üstü - sgk - işsizlik)
            vergi_matrah = asgari_ustu - asgari_ustu_sgk - asgari_ustu_issizlik
            
            # Gelir Vergisi (%15)
            gelir_vergisi = (vergi_matrah * Decimal('0.15')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Damga Vergisi (asgari üstü brütün %0.759'u)
            damga_vergisi = (asgari_ustu * Decimal('0.00759')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Toplam kesinti ve net maaş
        toplam_kesinti = sgk + issizlik + gelir_vergisi + damga_vergisi
        net_maas = (brut_maas - toplam_kesinti).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Debug çıktısı (geçici)
        print(f"HESAPLAMA DEBUG:")
        print(f"  Brüt Maaş: {brut_maas}")
        print(f"  Asgari Brüt: {asgari_brut}")
        print(f"  Asgari Üstü: {brut_maas - asgari_brut if brut_maas > asgari_brut else 0}")
        print(f"  SGK: {sgk}")
        print(f"  İşsizlik: {issizlik}")
        print(f"  Gelir Vergisi: {gelir_vergisi}")
        print(f"  Damga Vergisi: {damga_vergisi}")
        print(f"  Net Maaş: {net_maas}")
        
        return {
            'sgk_isci_payi': sgk,
            'issizlik_isci_payi': issizlik,
            'gelir_vergisi': gelir_vergisi,
            'damga_vergisi': damga_vergisi,
            'toplam_kesinti': toplam_kesinti,
            'net_maas': net_maas
        }
    
    def hesapla_isveren_maliyeti(self, brut_maas, personel):
        brut_maas = Decimal(str(brut_maas))
        sgk_orani = Decimal(0.2075)
        if personel and personel.tesvik_durumu:
            sgk_orani -= Decimal(0.05)
        sgk_isveren = brut_maas * sgk_orani
        issizlik_isveren = brut_maas * Decimal(0.02)
        toplam_maliyet = brut_maas + sgk_isveren + issizlik_isveren
        
        return {
            'sgk_isveren_payi': sgk_isveren,
            'issizlik_isveren_payi': issizlik_isveren,
            'isveren_toplam_maliyet': toplam_maliyet
        }
    
    # ==================== BORDRO OLUŞTURMA ====================
    
    @transaction.atomic
    def bordro_olustur(self, personel, ay, girilen_net_maas=None, girilen_brut_maas=None, 
                       fazla_mesai_saati=0, resmi_tatil_gun=0, bayram_gun=0, prim=0):
        
        # 1. Temel brüt maaşı hesapla
        if personel.maas_tipi == 'net':
            if girilen_net_maas:
                brut_maas = self.netten_brute(girilen_net_maas)
            else:
                brut_maas = self.netten_brute(personel.brut_maas)
        else:
            if girilen_brut_maas:
                brut_maas = Decimal(str(girilen_brut_maas))
            else:
                brut_maas = personel.brut_maas
        
        # 2. Ek ödemeleri hesapla
        fazla_mesai_tutari = self.fazla_mesai_hesapla(fazla_mesai_saati)
        resmi_tatil_tutari = self.resmi_tatil_hesapla(resmi_tatil_gun)
        bayram_tutari = self.bayram_hesapla(bayram_gun)
        
        # 3. Toplam brüt
        brut_toplam = brut_maas + fazla_mesai_tutari + resmi_tatil_tutari + bayram_tutari + Decimal(str(prim))
        
        # 4. Kesintiler ve net
        kesintiler = self.hesapla_kesintiler(brut_toplam, personel)
        isveren = self.hesapla_isveren_maliyeti(brut_toplam, personel)
        
        # 5. Bordro kaydı
        bordro, created = MaasBordrosu.objects.update_or_create(
            personel=personel,
            yil=self.yil,
            ay=ay,
            defaults={
                'brut_maas': brut_maas,
                'fazla_mesai_saati': fazla_mesai_saati,
                'fazla_mesai_tutari': fazla_mesai_tutari,
                'resmi_tatil_gun': resmi_tatil_gun,
                'resmi_tatil_tutari': resmi_tatil_tutari,
                'bayram_gun': bayram_gun,
                'bayram_tutari': bayram_tutari,
                'prim': prim,
                'sgk_isci_payi': kesintiler['sgk_isci_payi'],
                'issizlik_isci_payi': kesintiler['issizlik_isci_payi'],
                'gelir_vergisi': kesintiler['gelir_vergisi'],
                'damga_vergisi': kesintiler['damga_vergisi'],
                'toplam_kesinti': kesintiler['toplam_kesinti'],
                'net_maas': kesintiler['net_maas'],
                'sgk_isveren_payi': isveren['sgk_isveren_payi'],
                'issizlik_isveren_payi': isveren['issizlik_isveren_payi'],
                'isveren_toplam_maliyet': isveren['isveren_toplam_maliyet']
            }
        )
        return bordro