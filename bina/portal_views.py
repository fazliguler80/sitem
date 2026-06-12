# bina/portal_views.py - TAMAMEN DÜZELTİLMİŞ DOSYA

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.contrib.auth import update_session_auth_hash, authenticate, login
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from decimal import Decimal

from .models import (
    DaireKullanici, Aidat, Daire, Kisi, DaireIliskisi, Blok, 
    Depozito, DepozitoHareket, SiteAyarlari
)


# bina/portal_views.py - TAMAMEN DÜZELTİLMİŞ portal_ana_sayfa

@login_required(login_url='/portal/login/')
def portal_ana_sayfa(request):
    try:
        daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
        daire = daire_kullanici.daire
        
        # TÜM aidatları göster
        aidatlar = Aidat.objects.filter(daire=daire).order_by('-yil', '-ay')[:12]
        
        # Her aidat için açıklama oluştur
        for aidat in aidatlar:
            if not aidat.aciklama:
                if aidat.gider:
                    aidat.aciklama = f"{aidat.gider.get_tip_display()} gideri"
                else:
                    aidat.aciklama = f"{aidat.get_aidat_tipi_display()} aidatı"
        
        # TÜM ödenmemiş aidatlar
        toplam_borc = Aidat.objects.filter(
            daire=daire, 
            odeme_yapildi_mi=False
        ).aggregate(Sum('tutar'))['tutar__sum'] or 0
        
        print(f"DEBUG: {daire} için toplam borç: {toplam_borc}")
        
        # Her aidat için ödeme durumunu debug et
        for aidat in aidatlar:
            print(f"  {aidat.ay}/{aidat.yil} - {aidat.aidat_tipi} - odeme_yapildi_mi={aidat.odeme_yapildi_mi}")
        
        # DEPOZİTO BİLGİSİ - Burada depozito değişkenini tanımlıyoruz
        from .models import Depozito  # Güvenli import
        depozito_obj = Depozito.objects.filter(daire=daire, durum='alindi').first()
        
        if depozito_obj:
            depozito_tutari = float(depozito_obj.tutar)
            depozito_var = True
            print(f"DEBUG: Depozito bulundu - {depozito_tutari} TL")
        else:
            depozito_tutari = 0
            depozito_var = False
            print(f"DEBUG: Depozito bulunamadı")
        
        context = {
            'daire': daire,
            'kullanici': daire_kullanici,
            'aidatlar': aidatlar,
            'toplam_borc': toplam_borc,
            'depozito_var': depozito_var,
            'depozito_tutari': depozito_tutari,
        }
        return render(request, 'portal/ana_sayfa.html', context)
        
    except DaireKullanici.DoesNotExist:
        messages.error(request, 'Profiliniz bulunamadı.')
        return redirect('/portal/login/')
    except Exception as e:
        print(f"HATA: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Bir hata oluştu: {str(e)}')
        return redirect('/portal/login/')


@login_required
def aidat_gecmisi(request):
    try:
        daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
        daire = daire_kullanici.daire
        
        # TÜM aidatları al
        aidatlar = Aidat.objects.filter(daire=daire).order_by('-yil', '-ay')
        
        # Debug için konsola yazdır
        print("\n=== AİDAT_GEÇMİSİ DEBUG ===")
        for aidat in aidatlar:
            print(f"{aidat.ay}/{aidat.yil} - {aidat.aidat_tipi}: odeme_yapildi_mi={aidat.odeme_yapildi_mi}, tutar={aidat.tutar}")
        
        # Toplamlar
        toplam_odenen = sum(float(a.tutar) for a in aidatlar if a.odeme_yapildi_mi)
        toplam_borc = sum(float(a.tutar) for a in aidatlar if not a.odeme_yapildi_mi)
        
        print(f"Toplam ödenen: {toplam_odenen}")
        print(f"Toplam borç: {toplam_borc}")
        print("========================\n")
        
        context = {
            'aidatlar': aidatlar,
            'toplam_odenen': toplam_odenen,
            'toplam_borc': toplam_borc,
            'daire': daire,
        }
        return render(request, 'portal/aidat_gecmisi.html', context)
        
    except DaireKullanici.DoesNotExist:
        messages.error(request, 'Profiliniz bulunamadı.')
        return redirect('/portal/login/')
    except Exception as e:
        print(f"HATA: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Bir hata oluştu: {str(e)}')
        return redirect('/portal/')


@login_required
def borc_durumu(request):
    daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
    daire = daire_kullanici.daire
    
    # Kullanıcının birincil kişi olup olmadığını kontrol et
    birincil_kisi = DaireIliskisi.objects.filter(
        daire=daire, 
        kisi=daire_kullanici.kisi, 
        birincil_mi=True,
        aktif_mi=True
    ).exists()
    
    # Eğer birincil kişi değilse borçları gösterme
    if not birincil_kisi:
        context = {
            'borclar': [],
            'toplam_borc': 0,
            'daire': daire,
            'uyari': 'Bu daire için borç sorgulama yetkiniz bulunmamaktadır. Ana hesap sahibi ile iletişime geçiniz.'
        }
        return render(request, 'portal/borc_durumu.html', context)
    
    # TÜM ödenmemiş aidatlar (sabit aidatlar DAHİL) - odeme_yapildi_mi kullan
    borclar = Aidat.objects.filter(
        daire=daire, 
        odeme_yapildi_mi=False
    ).order_by('yil', 'ay')
    
    # Her borç için açıklama oluştur
    for borc in borclar:
        if not borc.aciklama:
            if borc.gider:
                borc.aciklama = f"{borc.gider.get_tip_display()} gideri - {borc.gider.tarih}"
            else:
                borc.aciklama = f"{borc.get_aidat_tipi_display()} - {borc.ay}/{borc.yil}"
    
    toplam_borc = borclar.aggregate(Sum('tutar'))['tutar__sum'] or 0
    
    context = {
        'borclar': borclar,
        'toplam_borc': toplam_borc,
        'daire': daire,
    }
    return render(request, 'portal/borc_durumu.html', context)


@login_required
def komsular(request, blok=None):
    daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
    mevcut_blok = daire_kullanici.daire.blok.blok_adi
    
    # Blok listesi
    bloklar = Blok.objects.all().values_list('blok_adi', flat=True).distinct()
    
    # Seçilen bloktaki daireler
    if blok:
        secili_blok = blok
        daireler = Daire.objects.filter(blok__blok_adi=blok)
    else:
        secili_blok = mevcut_blok
        daireler = Daire.objects.filter(blok__blok_adi=mevcut_blok)
    
    # Her daire için sakin bilgileri
    komsu_listesi = []
    for d in daireler:
        iliskiler = DaireIliskisi.objects.filter(daire=d, aktif_mi=True)
        sakinler = []
        for iliski in iliskiler:
            sakinler.append({
                'ad_soyad': iliski.kisi.ad_soyad,
                'telefon': iliski.kisi.telefon,
                'iliski': iliski.get_iliski_tipi_display(),
            })
        komsu_listesi.append({
            'daire_no': d.daire_no,
            'sakinler': sakinler,
        })
    
    context = {
        'komsular': komsu_listesi,
        'bloklar': bloklar,
        'secili_blok': secili_blok,
        'mevcut_blok': mevcut_blok,
        'daire': daire_kullanici.daire,
    }
    return render(request, 'portal/komsular.html', context)


@login_required
def profil_duzenle(request):
    daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
    
    if request.method == 'POST':
        # Kişisel bilgileri güncelle
        daire_kullanici.telefon = request.POST.get('telefon', daire_kullanici.telefon)
        daire_kullanici.email = request.POST.get('email', daire_kullanici.email)
        daire_kullanici.save()
        
        # Kişi modelini de güncelle (eğer ilişkiliyse)
        if daire_kullanici.kisi:
            daire_kullanici.kisi.telefon = daire_kullanici.telefon
            daire_kullanici.kisi.email = daire_kullanici.email
            daire_kullanici.kisi.save()
        
        # Şifre değişikliği
        sifre_form = PasswordChangeForm(request.user, request.POST)
        if sifre_form.is_valid():
            sifre_form.save()
            update_session_auth_hash(request, sifre_form.user)
            messages.success(request, 'Şifreniz başarıyla değiştirildi.')
        
        messages.success(request, 'Bilgileriniz güncellendi.')
        return redirect('profil_duzenle')
    
    context = {
        'daire_kullanici': daire_kullanici,
        'kisi': daire_kullanici.kisi,
    }
    return render(request, 'portal/profil_duzenle.html', context)


def portal_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            try:
                daire_kullanici = DaireKullanici.objects.get(kullanici=user)
                
                if daire_kullanici.ilk_giris or daire_kullanici.sifre_sifirlandi_mi:
                    # BURADA LOGIN YAPMA! Sadece session'a kaydet
                    request.session['must_change_password'] = True
                    request.session['user_id'] = user.id
                    return redirect('sifre_degistir_zorunlu')
                else:
                    login(request, user)
                    return redirect('portal_ana')
            except DaireKullanici.DoesNotExist:
                messages.error(request, 'Portal erişim yetkiniz bulunmamaktadır.')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı!')
    
    return render(request, 'portal/login.html')


#@login_required
def sifre_degistir_zorunlu(request):
    """İlk girişte zorunlu şifre değiştirme sayfası"""
    # Kullanıcı session'da mı kontrol et
    if not request.session.get('must_change_password', False):
        return redirect('portal_login')
    
    # Session'dan user_id'yi al
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('portal_login')
    
    # Kullanıcıyı bul
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('portal_login')
    
    # Kullanıcıyı authenticate et (login yapmadan)
    from django.contrib.auth import login
    login(request, user)
    
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            # Şifre değişti, ilk giriş ve sıfırlama flag'lerini kaldır
            daire_kullanici = DaireKullanici.objects.get(kullanici=user)
            daire_kullanici.ilk_giris = False
            daire_kullanici.sifre_sifirlandi_mi = False
            daire_kullanici.save()
            
            request.session.pop('must_change_password', None)
            messages.success(request, 'Şifreniz başarıyla değiştirildi. Ana sayfaya yönlendiriliyorsunuz.')
            return redirect('portal_ana')
    else:
        form = PasswordChangeForm(user)
    
    return render(request, 'portal/sifre_degistir_zorunlu.html', {'form': form})


def sifre_sifirla_confirm(request, uidb64, token):
    """Manuel şifre sıfırlama onay sayfası"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if new_password1 and new_password1 == new_password2:
                user.set_password(new_password1)
                user.save()
                
                # Şifre sıfırlandı bayraklarını güncelle
                try:
                    daire_kullanici = DaireKullanici.objects.get(kullanici=user)
                    daire_kullanici.ilk_giris = False
                    daire_kullanici.sifre_sifirlandi_mi = False
                    daire_kullanici.save()
                except DaireKullanici.DoesNotExist:
                    pass
                
                messages.success(request, 'Şifreniz başarıyla değiştirildi. Giriş yapabilirsiniz.')
                return redirect('portal_login')
            else:
                messages.error(request, 'Şifreler eşleşmiyor!')
        
        return render(request, 'portal/sifre_sifirla_confirm.html')
    else:
        messages.error(request, 'Geçersiz veya süresi dolmuş link!')
        return redirect('portal_login')


# ==================== DEPOZİTO VİEW'LARI ====================

# bina/portal_views.py - DÜZELTİLMİŞ depozito_gecmisi

@login_required
def depozito_gecmisi(request):
    """
    Portal kullanıcısının depozito geçmişini gösterir.
    """
    
    try:
        daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
        daire = daire_kullanici.daire
    except DaireKullanici.DoesNotExist:
        messages.error(request, "Daire bilginize ulaşılamadı.")
        return render(request, 'portal/depozito_gecmisi.html', {'hata': True})
    
    depozito = Depozito.objects.filter(daire=daire, durum='alindi').first()
    
    if not depozito:
        context = {
            'daire': daire,
            'depozito_var': False,
            'toplam_depozito': 0,
            'guncel_bakiye': 0,
            'hareketler': [],
            'yuvarlama_hareketleri': [],
            'toplam_yuvarlama_eklenen': 0,
            'toplam_yuvarlama_cikarilan': 0,
        }
        return render(request, 'portal/depozito_gecmisi.html', context)
    
    # Depozito hareketlerini al
    hareketler = depozito.hareketler.all().order_by('tarih', 'id')
    
    # Bakiye hesaplama ve hareketleri zenginleştirme
    bakiye = float(depozito.tutar)  # İlk depozito tutarı
    hareket_listesi = []
    yuvarlama_hareketleri = []
    toplam_yuvarlama_eklenen = 0
    toplam_yuvarlama_cikarilan = 0
    
    for hareket in hareketler:
        if hareket.hareket_tipi == 'ekleme':
            bakiye += float(hareket.tutar)
            islem_icon = '➕'
            renk = 'success'
            islem_aciklama = 'Depozitoya Eklendi'
        elif hareket.hareket_tipi == 'cikarma':
            bakiye -= float(hareket.tutar)
            islem_icon = '➖'
            renk = 'danger'
            islem_aciklama = 'Depozitodan Düşüldü'
        else:  # iade
            bakiye -= float(hareket.tutar)
            islem_icon = '↩️'
            renk = 'warning'
            islem_aciklama = 'İade Edildi'
        
        # Yuvarlama kaynaklı mı kontrol et
        yuvarlama_mi = 'yuvarlama' in hareket.aciklama.lower()
        
        if yuvarlama_mi:
            yuvarlama_hareketleri.append(hareket)
            if hareket.hareket_tipi == 'ekleme':
                toplam_yuvarlama_eklenen += float(hareket.tutar)
            elif hareket.hareket_tipi == 'cikarma':
                toplam_yuvarlama_cikarilan += float(hareket.tutar)
        
        hareket_listesi.append({
            'id': hareket.id,
            'tarih': hareket.tarih,
            'tarih_formatli': hareket.tarih.strftime('%d/%m/%Y'),
            'islem_tipi': hareket.get_hareket_tipi_display(),
            'islem_icon': islem_icon,
            'islem_aciklama': islem_aciklama,
            'renk': renk,
            'tutar': float(hareket.tutar),
            'bakiye': bakiye,
            'aciklama': hareket.aciklama,
            'yuvarlama_mi': yuvarlama_mi,
            'gider': hareket.gider,
        })
    
    site_ayar = SiteAyarlari.objects.first()
    
    # Debug için yazdır
    print(f"\n=== DEPOZITO OZETI ===")
    print(f"Yuvarlama hareket sayısı: {len(yuvarlama_hareketleri)}")
    print(f"Toplam yuvarlama eklenen: {toplam_yuvarlama_eklenen}")
    print(f"Toplam yuvarlama cikarilan: {toplam_yuvarlama_cikarilan}")
    print(f"Guncel bakiye: {bakiye}")
    
    context = {
        'daire': daire,
        'depozito': depozito,
        'depozito_var': True,
        'toplam_depozito': float(depozito.tutar),
        'guncel_bakiye': bakiye,
        'hareketler': hareket_listesi,
        'yuvarlama_hareketleri': yuvarlama_hareketleri,
        'toplam_yuvarlama_eklenen': toplam_yuvarlama_eklenen,
        'toplam_yuvarlama_cikarilan': toplam_yuvarlama_cikarilan,
        'site_ayar': site_ayar,
    }
    
    return render(request, 'portal/depozito_gecmisi.html', context)


@login_required
def depozito_detay(request, depozito_id):
    """
    Tek bir depozitonun detaylı hareket geçmişi
    """
    
    depozito = get_object_or_404(Depozito, id=depozito_id)
    
    # Kullanıcının yetkisini kontrol et
    try:
        daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
        if depozito.daire != daire_kullanici.daire:
            messages.error(request, "Bu depozito bilgisine erişim yetkiniz yok.")
            return redirect('depozito_gecmisi')
    except DaireKullanici.DoesNotExist:
        messages.error(request, "Daire bilginize ulaşılamadı.")
        return redirect('depozito_gecmisi')
    
    # Hareketleri al
    hareketler = depozito.hareketler.all().order_by('tarih', 'id')
    
    # Kümülatif bakiye hesapla
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
            'tarih_formatli': h.tarih.strftime('%d/%m/%Y'),
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
        'daire': depozito.daire,
    }
    
    return render(request, 'portal/depozito_detay.html', context)