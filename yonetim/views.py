from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from bina.models import Blok, Daire, Kisi, DaireIliskisi, Aidat
from bina.forms import BlokForm, DaireForm, KisiForm, DaireIliskisiForm, AidatForm

@login_required
def ana_sayfa(request):
    toplam_blok = Blok.objects.count()
    toplam_daire = Daire.objects.count()
    toplam_kisi = Kisi.objects.count()
    toplam_aidat = Aidat.objects.filter(odendi_mi=False).count()
    
    context = {
        'toplam_blok': toplam_blok,
        'toplam_daire': toplam_daire,
        'toplam_kisi': toplam_kisi,
        'toplam_aidat': toplam_aidat,
    }
    return render(request, 'yonetim/ana_sayfa.html', context)

@login_required
def blok_listesi(request):
    bloklar = Blok.objects.all()
    return render(request, 'yonetim/blok_listesi.html', {'bloklar': bloklar})

@login_required
def blok_ekle(request):
    if request.method == 'POST':
        form = BlokForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blok başarıyla eklendi!')
            return redirect('blok_listesi')
    else:
        form = BlokForm()
    return render(request, 'yonetim/blok_form.html', {'form': form, 'baslik': 'Blok Ekle'})

@login_required
def daire_ekle(request, blok_id=None):
    blok = None
    if blok_id:
        blok = get_object_or_404(Blok, id=blok_id)
    
    if request.method == 'POST':
        form = DaireForm(request.POST)
        if form.is_valid():
            daire = form.save(commit=False)
            if blok:
                daire.blok = blok
            daire.save()
            messages.success(request, f'{daire} başarıyla eklendi!')
            
            if 'devam' in request.POST:
                return redirect('daire_ekle', blok_id=blok.id if blok else None)
            return redirect('blok_detay', blok_id=daire.blok.id)
    else:
        form = DaireForm()
        if blok:
            form.fields['daire_no'].help_text = f'{blok} bloğuna daire ekliyorsunuz'
    
    return render(request, 'yonetim/daire_form.html', {
        'form': form, 
        'baslik': 'Daire Ekle',
        'blok': blok
    })

@login_required
def blok_detay(request, blok_id):
    blok = get_object_or_404(Blok, id=blok_id)
    daireler = blok.daireler.all()
    return render(request, 'yonetim/blok_detay.html', {'blok': blok, 'daireler': daireler})

@login_required
def kisi_listesi(request):
    kisiler = Kisi.objects.all()
    return render(request, 'yonetim/kisi_listesi.html', {'kisiler': kisiler})

@login_required
def kisi_ekle(request):
    if request.method == 'POST':
        form = KisiForm(request.POST)
        if form.is_valid():
            kisi = form.save()
            messages.success(request, f'{kisi.ad_soyad} başarıyla eklendi!')
            
            if 'devam_iliski' in request.POST:
                return redirect('daire_iliski_ekle', kisi_id=kisi.id)
            return redirect('kisi_listesi')
    else:
        form = KisiForm()
    
    return render(request, 'yonetim/kisi_form.html', {'form': form, 'baslik': 'Kişi Ekle'})

@login_required
def daire_iliski_ekle(request, kisi_id=None):
    if request.method == 'POST':
        form = DaireIliskisiForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Daire ilişkisi başarıyla eklendi!')
            return redirect('kisi_listesi')
    else:
        form = DaireIliskisiForm()
        if kisi_id:
            kisi = get_object_or_404(Kisi, id=kisi_id)
            form.fields['kisi'].initial = kisi
            form.fields['kisi'].widget.attrs['disabled'] = True
    
    # Daire seçenekleri için mevcut daireleri listele
    daireler = Daire.objects.all().select_related('blok')
    return render(request, 'yonetim/daire_iliski_form.html', {'form': form, 'daireler': daireler})

@login_required
def aidat_listesi(request):
    aidatlar = Aidat.objects.select_related('daire', 'kim_odedi').all()
    return render(request, 'yonetim/aidat_listesi.html', {'aidatlar': aidatlar})

@login_required
def aidat_ekle(request):
    if request.method == 'POST':
        form = AidatForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aidat başarıyla eklendi!')
            return redirect('aidat_listesi')
    else:
        form = AidatForm()
    
    return render(request, 'yonetim/aidat_form.html', {'form': form, 'baslik': 'Aidat Ekle'})

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from bina.models import Daire, Aidat, SiteAyarlari, Gider
from bina.utils import aylik_aidat_hesapla
from datetime import datetime
from django.db.models import Sum

@login_required
def aidat_raporu(request, yil=None, ay=None):
    """Aidat ve yakıt ödeme raporu"""
    
    # Varsayılan olarak içinde bulunduğumuz ayı al
    if not yil or not ay:
        now = datetime.now()
        yil = now.year
        ay = now.month
    
    # Site ayarlarını al
    site_ayar = SiteAyarlari.objects.first()
    
    # Tüm daireleri al
    daireler = Daire.objects.all().select_related('blok')
    
    # Aylar için Türkçe isimler
    aylar = {
        1: 'OCAK', 2: 'ŞUBAT', 3: 'MART', 4: 'NİSAN', 5: 'MAYIS',
        6: 'HAZİRAN', 7: 'TEMMUZ', 8: 'AĞUSTOS', 9: 'EYLÜL',
        10: 'EKİM', 11: 'KASIM', 12: 'ARALIK'
    }
    
    # Yakıt giderini bul (o aya ait)
    yakit_gideri = Gider.objects.filter(
        tip='yakıt',
        tarih__year=yil,
        tarih__month=ay
    ).first()
    
    # Her daire için aidat ve yakıt hesapla
    rapor_daireler = []
    toplam_aidat = 0
    toplam_yakit = 0
    toplam_genel = 0
    
    for daire in daireler:
        # Aidat miktarı (sabit veya hesaplanmış)
        aidat_miktari = float(site_ayar.sabit_aidat_miktari) if site_ayar and site_ayar.sabit_aidat_aktif_mi else 0
        
        # Yakıt miktarı (brüt metrekareye göre)
        yakit_miktari = 0
        if yakit_gideri:
            toplam_brut = sum([d.brut_metrekare or 0 for d in daireler if d.brut_metrekare])
            if toplam_brut > 0 and daire.brut_metrekare:
                yakit_miktari = float(yakit_gideri.tutar) * (daire.brut_metrekare / toplam_brut)
        
        # Daire tipine göre yuvarlama (isteğe bağlı)
        if daire.daire_tipi == '4+1_dublex':
            yakit_miktari = round(yakit_miktari / 10) * 10  # 10'a yuvarla
        elif daire.daire_tipi == '3+1_dublex':
            yakit_miktari = round(yakit_miktari / 10) * 10
        elif daire.daire_tipi == '4+1':
            yakit_miktari = round(yakit_miktari / 10) * 10
        else:  # 3+1
            yakit_miktari = round(yakit_miktari / 10) * 10
        
        toplam = aidat_miktari + yakit_miktari
        
        rapor_daireler.append({
            'daire_no': daire.daire_no,
            'blok': daire.blok.blok_adi,
            'daire_tipi': daire.get_daire_tipi_display(),
            'aidat': aidat_miktari,
            'yakit': yakit_miktari,
            'toplam': toplam,
        })
        
        toplam_aidat += aidat_miktari
        toplam_yakit += yakit_miktari
        toplam_genel += toplam
    
    # Daire tipine göre gruplandırma için
    tip_gruplari = {}
    for d in rapor_daireler:
        tip = d['daire_tipi']
        if tip not in tip_gruplari:
            tip_gruplari[tip] = {
                'aidat': d['aidat'],
                'yakit': d['yakit'],
                'toplam': d['toplam'],
                'adet': 1
            }
        else:
            tip_gruplari[tip]['yakit'] = d['yakit']  # Aynı tip aynı yakıt
            tip_gruplari[tip]['adet'] += 1
    
    # Site banka bilgileri
    banka = None
    if site_ayar:
        # İlk aktif banka hesabını al
        from bina.models import Banka
        banka = Banka.objects.filter(ana_hesap_mi=True).first()
    
    context = {
        'site_adi': site_ayar.site_adi if site_ayar else 'SİTE YÖNETİMİ',
        'ay_adi': aylar.get(ay, ''),
        'yil': yil,
        'odeme_tarihi': f"15.{ay:02d}.{yil}",
        'daireler': rapor_daireler,
        'tip_gruplari': tip_gruplari,
        'toplam_aidat': toplam_aidat,
        'toplam_yakit': toplam_yakit,
        'toplam_genel': toplam_genel,
        'banka_adi': banka.banka_adi if banka else 'SİTE YÖNETİMİ',
        'iban': banka.iban if banka else 'TR00 0000 0000 0000 0000 0000 00',
        'yakit_gideri': float(yakit_gideri.tutar) if yakit_gideri else 0,
    }
    
    return render(request, 'yonetim/aidat_raporu.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from bina.models import Daire, SiteAyarlari, Gider, Banka
from datetime import datetime

@login_required
def aidat_raporu(request, yil=None, ay=None):
    """Aidat ve yakıt ödeme raporu"""
    
    # Varsayılan olarak içinde bulunduğumuz ayı al
    if not yil or not ay:
        now = datetime.now()
        yil = now.year
        ay = now.month
    
    # Site ayarlarını al
    site_ayar = SiteAyarlari.objects.first()
    
    # Tüm daireleri al
    daireler = Daire.objects.all().select_related('blok')
    
    # Aylar için Türkçe isimler
    aylar = {
        1: 'OCAK', 2: 'ŞUBAT', 3: 'MART', 4: 'NİSAN', 5: 'MAYIS',
        6: 'HAZİRAN', 7: 'TEMMUZ', 8: 'AĞUSTOS', 9: 'EYLÜL',
        10: 'EKİM', 11: 'KASIM', 12: 'ARALIK'
    }
    
    # Yakıt giderini bul (o aya ait)
    yakit_gideri = Gider.objects.filter(
        tip='yakıt',
        tarih__year=yil,
        tarih__month=ay
    ).first()
    
    # Her daire için aidat ve yakıt hesapla
    rapor_daireler = []
    toplam_aidat = 0
    toplam_yakit = 0
    toplam_genel = 0
    
    for daire in daireler:
        # Aidat miktarı (sabit veya hesaplanmış)
        aidat_miktari = float(site_ayar.sabit_aidat_miktari) if site_ayar and site_ayar.sabit_aidat_aktif_mi else 0
        
        # Yakıt miktarı (brüt metrekareye göre)
        yakit_miktari = 0
        if yakit_gideri:
            toplam_brut = sum([d.brut_metrekare or 0 for d in daireler if d.brut_metrekare])
            if toplam_brut > 0 and daire.brut_metrekare:
                yakit_miktari = float(yakit_gideri.tutar) * (daire.brut_metrekare / toplam_brut)
        
        # 10 TL'ye yukarı yuvarla
        yakit_miktari = round(yakit_miktari / 10) * 10
        
        toplam = aidat_miktari + yakit_miktari
        
        rapor_daireler.append({
            'daire_no': daire.daire_no,
            'blok': daire.blok.blok_adi,
            'daire_tipi': daire.get_daire_tipi_display(),
            'aidat': aidat_miktari,
            'yakit': yakit_miktari,
            'toplam': toplam,
        })
        
        toplam_aidat += aidat_miktari
        toplam_yakit += yakit_miktari
        toplam_genel += toplam
    
    # Banka bilgileri
    banka = Banka.objects.filter(ana_hesap_mi=True).first()
    
    context = {
        'site_adi': site_ayar.site_adi if site_ayar else 'SİTE YÖNETİMİ',
        'ay_adi': aylar.get(ay, ''),
        'yil': yil,
        'odeme_tarihi': f"15.{ay:02d}.{yil}",
        'daireler': rapor_daireler,
        'toplam_aidat': toplam_aidat,
        'toplam_yakit': toplam_yakit,
        'toplam_genel': toplam_genel,
        'banka_adi': banka.banka_adi if banka else 'SİTE YÖNETİMİ',
        'iban': banka.iban if banka else 'TR00 0000 0000 0000 0000 0000 00',
        'yakit_gideri': float(yakit_gideri.tutar) if yakit_gideri else 0,
    }
    
    return render(request, 'yonetim/aidat_raporu.html', context)