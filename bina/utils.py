import math
from decimal import Decimal
from datetime import date
from .models import Gider, Daire, Depozito, DepozitoHareket, SiteAyarlari

def yuvarla_yukari(deger, yuvarlama_birimi=10):
    """Değeri yukarı yuvarla (örn: 2530 → 2550, 2520 → 2550)"""
    return math.ceil(deger / yuvarlama_birimi) * yuvarlama_birimi

def yakıt_ucreti_hesapla(gider_id):
    """
    Yakıt giderini hesapla, yukarı yuvarla ve farkı depozitoya ekle
    """
    try:
        gider = Gider.objects.get(id=gider_id)
    except Gider.DoesNotExist:
        return None
    
    if gider.tip != 'yakıt':
        return None
    
    daireler = Daire.objects.all()
    toplam_brut = sum([d.brut_metrekare or 0 for d in daireler if d.brut_metrekare])
    
    if toplam_brut == 0:
        return None
    
    sonuclar = []
    toplam_yuvarlanmis = 0
    
    for daire in daireler:
        if not daire.brut_metrekare:
            continue
            
        # Gerçek hesaplanan tutar
        gercek_tutar = float(gider.tutar) * (daire.brut_metrekare / toplam_brut)
        
        # Yuvarlanmış tutar (10 TL'ye yukarı yuvarla)
        yuvarlanmis_tutar = yuvarla_yukari(gercek_tutar, 10)
        
        # Fark (depozitoya eklenecek miktar)
        fark = yuvarlanmis_tutar - gercek_tutar
        
        sonuclar.append({
            'daire': str(daire),
            'daire_id': daire.id,
            'gercek_tutar': round(gercek_tutar, 2),
            'yuvarlanmis_tutar': yuvarlanmis_tutar,
            'fark': round(fark, 2)
        })
        toplam_yuvarlanmis += yuvarlanmis_tutar
    
    return {
        'gider': str(gider),
        'gider_tutari': float(gider.tutar),
        'toplam_yuvarlanmis': toplam_yuvarlanmis,
        'toplam_fark': toplam_yuvarlanmis - float(gider.tutar),
        'daireler': sonuclar
    }

def depozitoya_ekle(daire_id, miktar, aciklama, gider_id=None):
    """Fark tutarını depozitoya ekle"""
    from .models import Daire, Depozito, DepozitoHareket
    
    try:
        daire = Daire.objects.get(id=daire_id)
    except Daire.DoesNotExist:
        return None
    
    # Dairenin aktif depozitosunu bul veya oluştur
    depozito, created = Depozito.objects.get_or_create(
        daire=daire,
        durum='alindi',
        defaults={
            'kisi': None,
            'tutar': 0,
            'alinma_tarihi': date.today()
        }
    )
    
    # Depozito tutarını güncelle
    depozito.tutar += Decimal(str(miktar))
    depozito.save()
    
    # Hareket kaydı oluştur
    hareket = DepozitoHareket.objects.create(
        depozito=depozito,
        hareket_tipi='ekleme',
        tutar=miktar,
        tarih=date.today(),
        aciklama=aciklama,
        gider_id=gider_id
    )
    
    return hareket

def yakıt_gideri_kaydet_ve_depozito_ekle(gider_id):
    """Yakıt giderini kaydet, yuvarla ve depozitolara ekle"""
    hesaplama = yakıt_ucreti_hesapla(gider_id)
    if not hesaplama:
        return None
    
    eklenen_depozitolar = []
    for daire in hesaplama['daireler']:
        if daire['fark'] > 0:
            hareket = depozitoya_ekle(
                daire_id=daire['daire_id'],
                miktar=daire['fark'],
                aciklama=f"Yakıt gideri yuvarlama fazlası - {hesaplama['gider']}",
                gider_id=gider_id
            )
            if hareket:
                eklenen_depozitolar.append({
                    'daire': daire['daire'],
                    'fark': daire['fark'],
                    'depozito_yeni_tutar': float(hareket.depozito.tutar)
                })
    
    return {
        'gider': hesaplama['gider'],
        'toplam_yuvarlanmis': hesaplama['toplam_yuvarlanmis'],
        'toplam_fark': hesaplama['toplam_fark'],
        'depozito_eklenenler': eklenen_depozitolar
    }

def aylik_aidat_hesapla(ay, yil, daire=None):
    """
    Belirli bir ay için aidat hesapla
    - Sabit aidat varsa onu al
    - Varsa ekstra giderleri dağıt
    """
    site_ayar = SiteAyarlari.objects.first()
    if not site_ayar:
        return None
    
    # O aya ait giderler
    giderler = Gider.objects.filter(tarih__year=yil, tarih__month=ay)
    
    daireler = Daire.objects.all() if not daire else [daire]
    toplam_daire_sayisi = Daire.objects.count()
    toplam_brut = sum([d.brut_metrekare or 0 for d in daireler if d.brut_metrekare])
    toplam_arsa_payda = sum([d.arsa_pay_payda for d in daireler])
    
    sonuclar = []
    
    for daire_obj in daireler:
        # 1. Sabit aidat miktarı
        sabit_aidat = float(site_ayar.sabit_aidat_miktari) if site_ayar.sabit_aidat_aktif_mi else 0
        
        # 2. Ekstra giderlerden düşen pay
        ekstra_toplam = 0
        for gider in giderler:
            if gider.hesap_tipi == 'esit':
                pay = float(gider.tutar / toplam_daire_sayisi)
            elif gider.hesap_tipi == 'brut_metrekare':
                if toplam_brut > 0 and daire_obj.brut_metrekare:
                    pay = float(gider.tutar * (daire_obj.brut_metrekare / toplam_brut))
                else:
                    pay = 0
            elif gider.hesap_tipi == 'hisse':
                if toplam_arsa_payda > 0:
                    pay = float(gider.tutar * (daire_obj.arsa_pay_pay / toplam_arsa_payda))
                else:
                    pay = 0
            else:
                pay = 0
            ekstra_toplam += pay
        
        toplam_aidat = sabit_aidat + ekstra_toplam
        
        sonuclar.append({
            'daire': str(daire_obj),
            'daire_id': daire_obj.id,
            'blok': daire_obj.blok.blok_adi,
            'daire_no': daire_obj.daire_no,
            'brut_m2': daire_obj.brut_metrekare,
            'sabit_aidat': round(sabit_aidat, 2),
            'ekstra_gider': round(ekstra_toplam, 2),
            'toplam_aidat': round(toplam_aidat, 2)
        })
    
    return {
        'ay': ay,
        'yil': yil,
        'sabit_aidat_aktif': site_ayar.sabit_aidat_aktif_mi,
        'sabit_aidat_miktari': float(site_ayar.sabit_aidat_miktari),
        'toplam_gider': sum([float(g.tutar) for g in giderler]),
        'daireler': sonuclar
    }

def otomatik_aidat_ekle(ay, yil):
    """Tüm daireler için otomatik aidat kaydı oluştur"""
    from .models import Aidat
    
    hesaplama = aylik_aidat_hesapla(ay, yil)
    if not hesaplama:
        return None
    
    eklenenler = []
    for daire_aidat in hesaplama['daireler']:
        # Daha önce aidat kaydı var mı kontrol et
        try:
            daire_nesnesi = Daire.objects.get(id=daire_aidat['daire_id'])
            aidat, created = Aidat.objects.get_or_create(
                daire=daire_nesnesi,
                ay=ay,
                yil=yil,
                defaults={
                    'tutar': daire_aidat['toplam_aidat'],
                    'aidat_tipi': 'sabit' if hesaplama['sabit_aidat_aktif'] else 'diger',
                    'aciklama': f"Otomatik hesaplanan {ay}/{yil} aidatı"
                }
            )
            if created:
                eklenenler.append({
                    'daire': str(daire_nesnesi),
                    'tutar': float(aidat.tutar)
                })
        except Daire.DoesNotExist:
            continue
    
    return {
        'ay': ay,
        'yil': yil,
        'eklenen_aidat_sayisi': len(eklenenler),
        'aidatlar': eklenenler
    }