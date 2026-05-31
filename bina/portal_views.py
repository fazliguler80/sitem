from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import DaireKullanici, Aidat, Daire, Kisi, DaireIliskisi, Blok

@login_required(login_url='/portal/login/')
def portal_ana_sayfa(request):
    try:
        daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
        daire = daire_kullanici.daire
        
        # Sadece ekstra ve yakıt aidatlarını göster
        aidatlar = Aidat.objects.filter(
            daire=daire
        ).exclude(
            aidat_tipi='sabit'
        ).order_by('-yil', '-ay')[:12]
        
        # Her aidat için açıklama oluştur
        for aidat in aidatlar:
            if not aidat.aciklama:
                if aidat.gider:
                    aidat.aciklama = f"{aidat.gider.get_tip_display()} gideri"
                else:
                    aidat.aciklama = f"{aidat.get_aidat_tipi_display()} aidatı"
        
        toplam_borc = Aidat.objects.filter(
            daire=daire, 
            odendi_mi=False
        ).exclude(
            aidat_tipi='sabit'
        ).aggregate(Sum('tutar'))['tutar__sum'] or 0
        
        context = {
            'daire': daire,
            'kullanici': daire_kullanici,
            'aidatlar': aidatlar,
            'toplam_borc': toplam_borc,
        }
        return render(request, 'portal/ana_sayfa.html', context)
    except DaireKullanici.DoesNotExist:
        messages.error(request, 'Profiliniz bulunamadı.')
        return redirect('/portal/login/')
@login_required
def aidat_gecmisi(request):
    daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
    
    # Sadece ekstra ve yakıt aidatlarını göster
    aidatlar = Aidat.objects.filter(
        daire=daire_kullanici.daire
    ).exclude(
        aidat_tipi='sabit'
    ).order_by('-yil', '-ay')
    
    # Her aidat için açıklama oluştur
    for aidat in aidatlar:
        if not aidat.aciklama:
            if aidat.gider:
                aidat.aciklama = f"{aidat.gider.get_tip_display()} gideri - {aidat.gider.tarih}"
            else:
                aidat.aciklama = f"{aidat.get_aidat_tipi_display()} - {aidat.ay}/{aidat.yil}"
    
    toplam_odenen = aidatlar.filter(odendi_mi=True).aggregate(Sum('tutar'))['tutar__sum'] or 0
    toplam_borc = aidatlar.filter(odendi_mi=False).aggregate(Sum('tutar'))['tutar__sum'] or 0
    
    context = {
        'aidatlar': aidatlar,
        'toplam_odenen': toplam_odenen,
        'toplam_borc': toplam_borc,
        'daire': daire_kullanici.daire,
    }
    return render(request, 'portal/aidat_gecmisi.html', context)

@login_required
def borc_durumu(request):
    daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
    
    # Sadece ekstra ve yakıt aidatlarının ödenmemişlerini göster
    borclar = Aidat.objects.filter(
        daire=daire_kullanici.daire, 
        odendi_mi=False
    ).exclude(
        aidat_tipi='sabit'
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
        'daire': daire_kullanici.daire,
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

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

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

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.contrib import messages

def portal_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Daire kullanıcısı mı kontrol et
            try:
                daire_kullanici = DaireKullanici.objects.get(kullanici=user)
                
                # İlk giriş veya şifre sıfırlandı mı?
                if daire_kullanici.ilk_giris or daire_kullanici.sifre_sifirlandi_mi:
                    # Şifre değişikliği sayfasına yönlendir
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

@login_required
def sifre_degistir_zorunlu(request):
    """İlk girişte zorunlu şifre değiştirme sayfası"""
    if not request.session.get('must_change_password', False):
        return redirect('portal_ana')
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            # Şifre değişti, ilk giriş ve sıfırlama flag'lerini kaldır
            daire_kullanici = DaireKullanici.objects.get(kullanici=request.user)
            daire_kullanici.ilk_giris = False
            daire_kullanici.sifre_sifirlandi_mi = False
            daire_kullanici.save()
            
            request.session.pop('must_change_password', None)
            messages.success(request, 'Şifreniz başarıyla değiştirildi. Ana sayfaya yönlendiriliyorsunuz.')
            return redirect('portal_ana')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'portal/sifre_degistir_zorunlu.html', {'form': form})

from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User

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