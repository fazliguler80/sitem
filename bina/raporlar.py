from django.db.models import Sum, Q
from decimal import Decimal
from .models import Daire, Aidat, Gider, SiteAyarlari, DaireIliskisi, Kisi
from datetime import datetime, timedelta
from calendar import month_name

class SiteRaporlari:
    
    def __init__(self):
        self.site_ayar = SiteAyarlari.objects.first()
    
    def gelir_gider_raporu(self, yil, ay=None):
        """Gelir ve gider raporu"""
        if ay:
            giderler = Gider.objects.filter(tarih__year=yil, tarih__month=ay)
            aidatlar = Aidat.objects.filter(yil=yil, ay=ay)
            donem = f"{month_name[ay]} {yil}"
        else:
            giderler = Gider.objects.filter(tarih__year=yil)
            aidatlar = Aidat.objects.filter(yil=yil)
            donem = f"{yil} Yılı"
        
        toplam_gider = giderler.aggregate(Sum('tutar'))['tutar__sum'] or 0
        toplam_tahsilat = aidatlar.filter(odendi_mi=True).aggregate(Sum('tutar'))['tutar__sum'] or 0
        toplam_aidat = aidatlar.aggregate(Sum('tutar'))['tutar__sum'] or 0
        tahsilat_orani = (toplam_tahsilat / toplam_aidat * 100) if toplam_aidat > 0 else 0
        
        return {
            'donem': donem,
            'toplam_gider': float(toplam_gider),
            'toplam_tahsilat': float(toplam_tahsilat),
            'toplam_aidat': float(toplam_aidat),
            'tahsilat_orani': round(tahsilat_orani, 2),
            'bakiye': float(toplam_tahsilat - toplam_gider),
            'gider_detay': [
                {'tip': g.get_tip_display(), 'tutar': float(g.tutar), 'tarih': g.tarih}
                for g in giderler
            ]
        }
    
    def daire_bazli_aidat_raporu(self, yil, ay=None):
        """Daire bazlı aidat ve ödeme durumu"""
        if ay:
            aidatlar = Aidat.objects.filter(yil=yil, ay=ay)
            donem = f"{month_name[ay]} {yil}"
        else:
            aidatlar = Aidat.objects.filter(yil=yil)
            donem = f"{yil} Yılı"
        
        rapor = []
        daireler = Daire.objects.all()
        
        for daire in daireler:
            daire_aidat = aidatlar.filter(daire=daire)
            toplam_borc = daire_aidat.aggregate(Sum('tutar'))['tutar__sum'] or 0
            odenen = daire_aidat.filter(odendi_mi=True).aggregate(Sum('tutar'))['tutar__sum'] or 0
            gecikme_faizi = daire_aidat.aggregate(Sum('gecikme_faizi'))['gecikme_faizi__sum'] or 0
            
            # Daire sakinlerini bul
            iliskiler = DaireIliskisi.objects.filter(daire=daire, aktif_mi=True)
            sakinler = [f"{i.kisi.ad_soyad} ({i.get_iliski_tipi_display()})" for i in iliskiler]
            
            rapor.append({
                'daire': str(daire),
                'blok': daire.blok.blok_adi,
                'daire_no': daire.daire_no,
                'brut_m2': daire.brut_metrekare,
                'arsa_pay': f"{daire.arsa_pay_pay}/{daire.arsa_pay_payda}",
                'sakinler': ' - '.join(sakinler) if sakinler else 'Kayıtlı Değil',
                'toplam_borc': float(toplam_borc),
                'odenen': float(odenen),
                'kalan_borc': float(toplam_borc - odenen),
                'gecikme_faizi': float(gecikme_faizi),
                'durum': 'Ödendi' if toplam_borc == odenen else ('Kısmi Ödendi' if odenen > 0 else 'Ödenmedi')
            })
        
        return {
            'donem': donem,
            'toplam_borc': sum([r['toplam_borc'] for r in rapor]),
            'toplam_odenen': sum([r['odenen'] for r in rapor]),
            'toplam_kalan': sum([r['kalan_borc'] for r in rapor]),
            'daireler': rapor
        }
    
    def gider_dagitim_raporu(self, gider_id):
        """Bir giderin dairelere dağıtım raporu"""
        gider = Gider.objects.get(id=gider_id)
        daireler = Daire.objects.all()
        
        # Toplam değerleri hesapla
        toplam_daire = daireler.count()
        toplam_brut = sum([d.brut_metrekare or 0 for d in daireler])
        toplam_arsa_payda = sum([d.arsa_pay_payda for d in daireler])
        
        dagitim = []
        for daire in daireler:
            if gider.hesap_tipi == 'esit':
                tutar = float(gider.tutar / toplam_daire)
                formül = f"{gider.tutar} TL / {toplam_daire} daire"
            elif gider.hesap_tipi == 'brut_metrekare':
                tutar = float(gider.tutar * (daire.brut_metrekare / toplam_brut)) if toplam_brut > 0 else 0
                formül = f"{gider.tutar} TL × ({daire.brut_metrekare} / {toplam_brut})"
            elif gider.hesap_tipi == 'hisse':
                tutar = float(gider.tutar * (daire.arsa_pay_pay / toplam_arsa_payda)) if toplam_arsa_payda > 0 else 0
                formül = f"{gider.tutar} TL × ({daire.arsa_pay_pay}/{daire.arsa_pay_payda})"
            else:
                tutar = 0
                formül = "-"
            
            dagitim.append({
                'daire': str(daire),
                'blok': daire.blok.blok_adi,
                'daire_no': daire.daire_no,
                'brut_m2': daire.brut_metrekare,
                'arsa_pay': f"{daire.arsa_pay_pay}/{daire.arsa_pay_payda}",
                'tutar': round(tutar, 2),
                'formul': formül
            })
        
        return {
            'gider_tipi': gider.get_tip_display(),
            'hesap_tipi': gider.get_hesap_tipi_display(),
            'toplam_tutar': float(gider.tutar),
            'tarih': gider.tarih,
            'dagitim': dagitim
        }
    
    def aylik_rapor(self, yil, ay):
        """Aylık özet rapor"""
        gelir_gider = self.gelir_gider_raporu(yil, ay)
        aidat_raporu = self.daire_bazli_aidat_raporu(yil, ay)
        
        return {
            'yil': yil,
            'ay': ay,
            'ay_adi': month_name[ay],
            'gelir_gider': gelir_gider,
            'aidat_durumu': aidat_raporu,
            'odeme_basari_orani': gelir_gider['tahsilat_orani']
        }
    
    def yillik_ozet_rapor(self, yil):
        """Yıllık özet rapor"""
        aylik_raporlar = []
        for ay in range(1, 13):
            aylik_raporlar.append(self.gelir_gider_raporu(yil, ay))
        
        toplam_gelir = sum([r['toplam_tahsilat'] for r in aylik_raporlar])
        toplam_gider = sum([r['toplam_gider'] for r in aylik_raporlar])
        
        return {
            'yil': yil,
            'aylik_raporlar': aylik_raporlar,
            'yillik_toplam_gelir': toplam_gelir,
            'yillik_toplam_gider': toplam_gider,
            'yillik_net_kar': toplam_gelir - toplam_gider
        }
    
    def gecikme_raporu(self):
        """Gecikmiş aidat raporu"""
        bugun = datetime.now().date()
        gecikmis_aidatlar = Aidat.objects.filter(
            odendi_mi=False,
            yil__lte=bugun.year
        )
        
        rapor = []
        for aidat in gecikmis_aidatlar:
            gecikme_gun = (bugun - datetime(aidat.yil, 1, 1).date()).days if aidat.ay else 0
            faiz = aidat.tutar * (self.site_ayar.gecikme_faizi_orani / 100) if self.site_ayar else 0
            
            rapor.append({
                'daire': str(aidat.daire),
                'ay': aidat.ay,
                'yil': aidat.yil,
                'tutar': float(aidat.tutar),
                'gecikme_gun': gecikme_gun,
                'faiz': float(faiz),
                'toplam_borc': float(aidat.tutar + faiz)
            })
        
        return {
            'toplam_gecikmis_aidat': len(rapor),
            'toplam_gecikmis_tutar': sum([r['tutar'] for r in rapor]),
            'toplam_faiz': sum([r['faiz'] for r in rapor]),
            'gecikmeler': rapor
        }