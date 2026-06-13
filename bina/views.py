# portal/views.py veya ana views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bina.models import DaireKullanici, Depozito, DepozitoHareket

@login_required(login_url='/portal/login/')
def portal_depozito_gecmisi(request):
    """Portal kullanıcısının depozito geçmişini göster"""
    
    # Giriş yapan kullanıcının daire bilgisini bul
    try:
        daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
        daire = daire_kullanici.daire
    except DaireKullanici.DoesNotExist:
        messages.error(request, "Daire bilginize ulaşılamadı.")
        return render(request, 'portal/depozito_gecmisi.html', {'error': True})
    
    # Dairenin aktif depozitosunu bul
    depozito = Depozito.objects.filter(daire=daire, durum='alindi').first()
    
    if not depozito:
        # Depozito kaydı yoksa
        context = {
            'daire': daire,
            'depozito_var': False,
            'gecmis_hareketler': [],
            'toplam_depozito': 0
        }
        return render(request, 'portal/depozito_gecmisi.html', context)
    
    # Depozito hareketlerini al (en eski -> en yeni)
    hareketler = depozito.hareketler.all().order_by('tarih', 'id')
    
    # Her harekete bakiye bilgisi ekle
    bakiye = 0
    hareket_listesi = []
    
    for hareket in hareketler:
        if hareket.hareket_tipi == 'ekleme':
            bakiye += float(hareket.tutar)
            islem_tip = 'depozito_eklendi'
            islem_icon = '➕'
            renk = 'success'
        elif hareket.hareket_tipi == 'cikarma':
            bakiye -= float(hareket.tutar)
            islem_tip = 'depozito_eksildi'
            islem_icon = '➖'
            renk = 'danger'
        else:  # iade
            bakiye -= float(hareket.tutar)
            islem_tip = 'depozito_iade'
            islem_icon = '↩️'
            renk = 'warning'
        
        hareket_listesi.append({
            'tarih': hareket.tarih,
            'islem_tipi': hareket.get_hareket_tipi_display(),
            'islem_tip_kodu': islem_tip,
            'islem_icon': islem_icon,
            'renk': renk,
            'tutar': float(hareket.tutar),
            'bakiye': bakiye,
            'aciklama': hareket.aciklama,
            'gider': hareket.gider  # Bağlı gider varsa
        })
    
    context = {
        'daire': daire,
        'depozito': depozito,
        'depozito_var': True,
        'toplam_depozito': bakiye,  # ← ARTIK HAREKETLERLE TOPLAM
        'guncel_bakiye': bakiye,
        'gecmis_hareketler': hareket_listesi,
    }
    
    return render(request, 'portal/depozito_gecmisi.html', context)


@login_required(login_url='/portal/login/')
def portal_depozito_detay(request, depozito_id):
    """Tek bir depozitonun detaylı geçmişi"""
    
    depozito = get_object_or_404(Depozito, id=depozito_id)
    
    # Kullanıcının bu depozitoya erişim yetkisi var mı kontrol et
    try:
        daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
        if depozito.daire != daire_kullanici.daire:
            messages.error(request, "Bu depozito bilgisine erişim yetkiniz yok.")
            return redirect('portal_depozito_gecmisi')
    except DaireKullanici.DoesNotExist:
        messages.error(request, "Daire bilginize ulaşılamadı.")
        return redirect('portal_depozito_gecmisi')
    
    hareketler = depozito.hareketler.all().order_by('tarih', 'id')
    
    # Bakiye hesaplama
    bakiye = 0
    hareket_listesi = []
    
    for h in hareketler:
        if h.hareket_tipi == 'ekleme':
            bakiye += float(h.tutar)
        elif h.hareket_tipi in ['cikarma', 'iade']:
            bakiye -= float(h.tutar)
        
        hareket_listesi.append({
            'id': h.id,
            'tarih': h.tarih,
            'islem_tipi': h.get_hareket_tipi_display(),
            'tutar': float(h.tutar),
            'bakiye': bakiye,
            'aciklama': h.aciklama,
            'gider': h.gider,
        })
    
    context = {
        'depozito': depozito,
        'hareketler': hareket_listesi,
        'toplam_tutar': float(depozito.tutar),
        'guncel_bakiye': bakiye,
    }
    
    return render(request, 'portal/depozito_detay.html', context)

def home_page(request):
    """Ana sayfa görünümü"""
    return render(request, 'home.html')