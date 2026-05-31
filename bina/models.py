from django.db import models
from django.contrib.auth.models import User
from datetime import date
import random
import string
from django.core.mail import send_mail
from django.conf import settings

class SiteAyarlari(models.Model):
    """Sitenin genel ayarları ve sabit bilgileri"""
    site_adi = models.CharField(max_length=200, verbose_name="Site Adı")
    adres = models.TextField(verbose_name="Adres")
    il = models.CharField(max_length=50, verbose_name="İl")
    ilce = models.CharField(max_length=50, verbose_name="İlçe")
    posta_kodu = models.CharField(max_length=10, blank=True, verbose_name="Posta Kodu")
    telefon = models.CharField(max_length=15, verbose_name="Telefon")
    email = models.EmailField(verbose_name="E-posta")
    
    # Arsa bilgileri
    toplam_arsa_m2 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Toplam Arsa (m²)")
    
    # Abonelik bilgileri
    elektrik_abone_no = models.CharField(max_length=50, blank=True, verbose_name="Elektrik Abone No")
    su_abone_no = models.CharField(max_length=50, blank=True, verbose_name="Su Abone No")
    dogalgaz_abone_no = models.CharField(max_length=50, blank=True, verbose_name="Doğalgaz Abone No")
    
    # Site görevlileri
    apartman_gorevlisi = models.CharField(max_length=100, blank=True, verbose_name="Apartman Görevlisi")
    guvenlik_gorevlisi = models.CharField(max_length=100, blank=True, verbose_name="Güvenlik Görevlisi")
    bahcivan = models.CharField(max_length=100, blank=True, verbose_name="Bahçıvan")
    
    # Banka bilgileri
    banka_adi = models.CharField(max_length=100, blank=True, verbose_name="Banka Adı")
    iban = models.CharField(max_length=34, blank=True, verbose_name="IBAN")
    hesap_sahibi = models.CharField(max_length=100, blank=True, verbose_name="Hesap Sahibi")
    
    # Yönetim bilgileri
    yonetim_kurulu_baskani = models.CharField(max_length=100, blank=True, verbose_name="Yönetim Kurulu Başkanı")
    yonetim_kurulu_uyeleri = models.TextField(blank=True, verbose_name="Yönetim Kurulu Üyeleri")
    denetci = models.CharField(max_length=100, blank=True, verbose_name="Denetçi")
    
    # Diğer
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    def __str__(self):
        return self.site_adi
    
    class Meta:
        verbose_name = "Site Ayarı"
        verbose_name_plural = "Site Ayarları"
    
    def save(self, *args, **kwargs):
        # Sadece bir tane site ayarı olmasını sağla
        if not self.pk and SiteAyarlari.objects.exists():
            raise ValueError("Sadece bir Site Ayarı kaydı olabilir!")
        super().save(*args, **kwargs)

class Blok(models.Model):
    BLOK_LAR = [
        ('A', 'A Blok'),
        ('B', 'B Blok'),
        ('C', 'C Blok'),
        ('D', 'D Blok'),
        ('E', 'E Blok'),
    ]
    blok_adi = models.CharField(max_length=1, choices=BLOK_LAR, unique=True, verbose_name="Blok Adı")
    kat_sayisi = models.IntegerField(default=4, verbose_name="Kat Sayısı")
    daire_sayisi = models.IntegerField(default=16, verbose_name="Toplam Daire Sayısı")
    
    def __str__(self):
        return f"{self.get_blok_adi_display()}"
    
    class Meta:
        verbose_name = "Blok"
        verbose_name_plural = "Bloklar"

class Daire(models.Model):
    TASINMAZ_TIPI = [
        ('kat_mulkiyeti', 'Kat Mülkiyeti'),
        ('kat_irtifaki', 'Kat İrtifakı'),
        ('diger', 'Diğer'),
    ]
    
    NITELIK_TIPI = [
        ('mesken', 'Mesken'),
        ('dukkan', 'Dükkan'),
        ('depo', 'Depo'),
        ('ofis', 'Ofis'),
        ('diger', 'Diğer'),
    ]
    
    DAIRE_TIPLERI = [
        ('1+0', '1+0 (Stüdyo)'),
        ('1+1', '1+1'),
        ('2+1', '2+1'),
        ('3+1', '3+1'),
        ('3+1_dublex', '3+1 Dublex'),
        ('4+1', '4+1'),
        ('4+1_dublex', '4+1 Dublex'),
        ('5+1', '5+1'),
        ('5+1_dublex', '5+1 Dublex'),
        ('6+1', '6+1'),
        ('diger', 'Diğer'),
    ]
    
    blok = models.ForeignKey(Blok, on_delete=models.CASCADE, verbose_name="Blok", related_name='daireler')
    daire_no = models.CharField(max_length=10, verbose_name="Daire No")
    daire_tipi = models.CharField(max_length=20, choices=DAIRE_TIPLERI, verbose_name="Daire Tipi")
    
    # Taşınmaz bilgileri
    tasinmaz_tipi = models.CharField(max_length=20, choices=TASINMAZ_TIPI, default='kat_mulkiyeti', verbose_name="Taşınmaz Tipi")
    nitelik = models.CharField(max_length=20, choices=NITELIK_TIPI, default='mesken', verbose_name="Nitelik")
    
    # Arsa payı bilgileri (KESİR olarak - m² DEĞİL!)
    arsa_pay_pay = models.IntegerField(default=1, verbose_name="Arsa Payı (Pay)", 
                                       help_text="Örnek: 48 (48/2700 pay için)")
    arsa_pay_payda = models.IntegerField(default=10000, verbose_name="Arsa Payı (Payda)",
                                         help_text="Örnek: 2700 (48/2700 pay için)")
    
    # Hisse oranı (otomatik hesaplanır)
    hisse_orani = models.DecimalField(max_digits=10, decimal_places=6, default=0.0001, 
                                      help_text="Otomatik hesaplanır: Pay/Payda", 
                                      verbose_name="Hisse Oranı")
    
    # Fiziksel özellikler
    kat = models.IntegerField(default=1, verbose_name="Bulunduğu Kat")
    net_metrekare = models.IntegerField(null=True, blank=True, verbose_name="Net Metrekare", 
                                        help_text="Dairenin iç net alanı (m²)")
    brut_metrekare = models.IntegerField(null=True, blank=True, verbose_name="Brüt Metrekare",
                                         help_text="Duvarlar dahil toplam alan (m²) - YAKIT HESABI İÇİN")
    balkon_m2 = models.IntegerField(null=True, blank=True, verbose_name="Balkon Alanı (m²)")
    oda_sayisi = models.IntegerField(default=3, verbose_name="Oda Sayısı")
    
    # Tapu bilgileri
    tapu_kayit_no = models.CharField(max_length=50, blank=True, verbose_name="Tapu Kayıt No")
    tapu_sahibi = models.CharField(max_length=100, blank=True, verbose_name="Tapu Sahibi")
    tapu_tarihi = models.DateField(null=True, blank=True, verbose_name="Tapu Tarihi")
    
    def __str__(self):
        return f"{self.blok} - {self.daire_no} Nolu Daire (Arsa Payı: {self.arsa_pay_pay}/{self.arsa_pay_payda})"
    
    def arsa_pay_m2_hesapla(self, toplam_arsa_m2):
        """Arsa payının metrekaresini hesapla (sadece bilgi amaçlı)"""
        if self.arsa_pay_payda > 0:
            return (toplam_arsa_m2 * self.arsa_pay_pay) / self.arsa_pay_payda
        return 0
    
    def arsa_pay_yuzdesi(self):
        """Arsa payının yüzdesini hesapla"""
        if self.arsa_pay_payda > 0:
            return (self.arsa_pay_pay / self.arsa_pay_payda) * 100
        return 0
    
    def save(self, *args, **kwargs):
        # Hisse oranını otomatik hesapla (Toplam arsaya göre)
        try:
            site_ayar = SiteAyarlari.objects.first()
            if site_ayar and site_ayar.toplam_arsa_m2 > 0:
                # Hisse oranı = (Arsa Payı Kesiri) / Toplam Arsa
                arsa_pay_kesir = self.arsa_pay_pay / self.arsa_pay_payda if self.arsa_pay_payda > 0 else 0
                
                # Net hisse oranı (gider dağıtımında kullanılacak)
                self.hisse_orani = arsa_pay_kesir
                
                # Alternatif: Brüt metrekareye göre hisse (opsiyonel)
                if site_ayar.toplam_brut_m2 and self.brut_metrekare:
                    self.hisse_orani_brut = self.brut_metrekare / site_ayar.toplam_brut_m2
        except:
            pass
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Daire"
        verbose_name_plural = "Daireler"
        unique_together = ['blok', 'daire_no']

class DaireKullanici(models.Model):
    """Daire sakinleri için özel kullanıcı profili"""
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Kullanıcı", null=True, blank=True)
    daire = models.ForeignKey('Daire', on_delete=models.CASCADE, verbose_name="Daire")
    kisi = models.ForeignKey('Kisi', on_delete=models.CASCADE, verbose_name="Daire Sakini", null=True, blank=True)
    telefon = models.CharField(max_length=15, verbose_name="Telefon")
    email = models.EmailField(verbose_name="E-posta")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    def __str__(self):
        if self.kullanici:
            return f"{self.kullanici.get_full_name()} - {self.daire}"
        elif self.kisi:
            return f"{self.kisi.ad_soyad} - {self.daire}"
        return f"{self.daire}"
    
    def save(self, *args, **kwargs):
        # Eğer kişi seçildiyse ve kullanıcı yoksa otomatik oluştur
        if self.kisi and not self.kullanici:
            # Kullanıcı adı oluştur (örn: fazliguler)
            ad_soyad = self.kisi.ad_soyad.lower().replace(' ', '').replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
            kullanici_adi = ad_soyad
            
            # Aynı kullanıcı adı varsa daire no ekle
            if User.objects.filter(username=kullanici_adi).exists():
                kullanici_adi = f"{kullanici_adi}{self.daire.daire_no}"
            
            # Rastgele şifre oluştur (kullanıcı daha sonra değiştirebilir)
            import random
            import string
            sifre = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            
            # Kullanıcı oluştur
            user = User.objects.create_user(
                username=kullanici_adi,
                password=sifre,
                first_name=self.kisi.ad_soyad.split()[0] if ' ' in self.kisi.ad_soyad else self.kisi.ad_soyad,
                last_name=self.kisi.ad_soyad.split()[-1] if ' ' in self.kisi.ad_soyad else '',
                email=self.email
            )
            self.kullanici = user
            
            # Telefon ve email bilgilerini kişiden al
            if not self.telefon and self.kisi.telefon:
                self.telefon = self.kisi.telefon
            if not self.email and self.kisi.email:
                self.email = self.kisi.email
        
        super().save(*args, **kwargs)

    def _olustur_sifre(self, uzunluk=10):
        """Rastgele şifre oluştur"""
        karakterler = string.ascii_letters + string.digits
        return ''.join(random.choices(karakterler, k=uzunluk))
    
    def _kullanici_adi_olustur(self):
        """Kullanıcı adı oluştur (örn: fazliguler1)"""
        ad_soyad = self.kisi.ad_soyad.lower()
        ad_soyad = ad_soyad.replace(' ', '').replace('ı', 'i').replace('ğ', 'g')
        ad_soyad = ad_soyad.replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
        
        kullanici_adi = ad_soyad
        sayac = 1
        while User.objects.filter(username=kullanici_adi).exists():
            kullanici_adi = f"{ad_soyad}{sayac}"
            sayac += 1
        return kullanici_adi
    
    def _sifre_gonder(self, sifre):
        """E-posta ve SMS ile şifre gönder"""
        # E-posta gönder
        konu = f"Site Yönetim Portalı - {self.daire} Giriş Bilgileriniz"
        mesaj = f"""
Sayın {self.kisi.ad_soyad},

Site yönetim portalına giriş yapabilmeniz için bilgileriniz oluşturulmuştur.

🌐 Giriş Adresi: http://127.0.0.1:8000/portal/login/
👤 Kullanıcı Adı: {self.kullanici.username}
🔑 Şifre: {sifre}

İlk girişinizde şifrenizi değiştirmeniz önerilir.

İyi günler dileriz.
{self.daire.blok.site_ayar.site_adi if hasattr(self.daire.blok, 'site_ayar') else 'Site Yönetimi'}
"""
        try:
            send_mail(konu, mesaj, settings.DEFAULT_FROM_EMAIL, [self.email], fail_silently=False)
        except:
            pass
        
        # SMS gönder (opsiyonel - SMS API entegrasyonu gerekir)
        # if self.telefon:
        #     self._sms_gonder(self.telefon, f"Portal şifreniz: {sifre}")
    
    def save(self, *args, **kwargs):
        if self.kisi and not self.kullanici:
            # Kullanıcı adı oluştur
            kullanici_adi = self._kullanici_adi_olustur()
            
            # Şifre oluştur
            sifre = self._olustur_sifre()
            
            # Kullanıcı oluştur
            user = User.objects.create_user(
                username=kullanici_adi,
                password=sifre,
                first_name=self.kisi.ad_soyad.split()[0] if ' ' in self.kisi.ad_soyad else self.kisi.ad_soyad,
                last_name=self.kisi.ad_soyad.split()[-1] if ' ' in self.kisi.ad_soyad else '',
                email=self.email
            )
            self.kullanici = user
            
            # Telefon ve email bilgilerini kişiden al
            if not self.telefon and self.kisi.telefon:
                self.telefon = self.kisi.telefon
            if not self.email and self.kisi.email:
                self.email = self.kisi.email
            
            # Şifreyi kaydet (geçici olarak - admin görmesi için)
            self._yeni_sifre = sifre
        
        super().save(*args, **kwargs)
        
        # Şifre gönder (kayıttan sonra)
        if hasattr(self, '_yeni_sifre'):
            self._sifre_gonder(self._yeni_sifre)
            delattr(self, '_yeni_sifre')
    
    sifre_sifirlandi_mi = models.BooleanField(default=False, verbose_name="Şifre Sıfırlandı mı?")
    ilk_giris = models.BooleanField(default=True, verbose_name="İlk Giriş")
    
    def sifre_sifirla(self, admin_request=False):
        """Şifre sıfırlama"""
        import random
        import string
        yeni_sifre = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        self.kullanici.set_password(yeni_sifre)
        self.kullanici.save()
        self.sifre_sifirlandi_mi = True
        self.ilk_giris = True
        self.save()
        
        if admin_request:
            return yeni_sifre
        return None
    
    class Meta:
        verbose_name = "Daire Kullanıcısı"
        verbose_name_plural = "Daire Kullanıcıları"

class Kisi(models.Model):
    KISI_TIPI = [
        ('ev_sahibi', 'Ev Sahibi'),
        ('kiraci', 'Kiracı'),
    ]
    
    ad_soyad = models.CharField(max_length=100, verbose_name="Ad Soyad")
    kisi_tipi = models.CharField(max_length=20, choices=KISI_TIPI, verbose_name="Kişi Tipi")
    tc_kimlik = models.CharField(max_length=11, blank=True, verbose_name="TC Kimlik No")
    telefon = models.CharField(max_length=15, verbose_name="Telefon")
    cep_telefonu = models.CharField(max_length=15, blank=True, verbose_name="Cep Telefonu")
    is_telefonu = models.CharField(max_length=15, blank=True, verbose_name="İş Telefonu")
    email = models.EmailField(blank=True, verbose_name="E-posta")
    adres = models.TextField(blank=True, verbose_name="Adres")
    acil_durum_kisisi = models.CharField(max_length=100, blank=True, verbose_name="Acil Durum Kişisi")
    acil_durum_tel = models.CharField(max_length=15, blank=True, verbose_name="Acil Durum Telefonu")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    
    def __str__(self):
        return f"{self.ad_soyad} ({self.get_kisi_tipi_display()})"
    
    class Meta:
        verbose_name = "Kişi"
        verbose_name_plural = "Kişiler"

class DaireIliskisi(models.Model):
    daire = models.ForeignKey(Daire, on_delete=models.CASCADE, verbose_name="Daire", related_name='iliskiler')
    kisi = models.ForeignKey(Kisi, on_delete=models.CASCADE, verbose_name="Kişi", related_name='daire_iliskileri')
    iliski_tipi = models.CharField(max_length=20, choices=Kisi.KISI_TIPI, verbose_name="İlişki Tipi")
    baslangic_tarihi = models.DateField(default=date.today, verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    kira_tutari = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Kira Tutarı (TL)")
    
    def __str__(self):
        return f"{self.daire} - {self.kisi} ({self.get_iliski_tipi_display()})"
    
    class Meta:
        verbose_name = "Daire İlişkisi"
        verbose_name_plural = "Daire İlişkileri"

class Aidat(models.Model):
    AIDAT_TIPI = [
        ('sabit', 'Sabit Aidat'),
        ('ekstra', 'Ekstra Gider Aidatı'),
        ('yakıt', 'Yakıt Aidatı'),
        ('diger', 'Diğer'),
    ]
    
    daire = models.ForeignKey(Daire, on_delete=models.CASCADE, verbose_name="Daire")
    ay = models.CharField(max_length=20, verbose_name="Ay")
    yil = models.IntegerField(default=date.today().year, verbose_name="Yıl")
    tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Aidat Tutarı")
    aidat_tipi = models.CharField(max_length=20, choices=AIDAT_TIPI, default='sabit', verbose_name="Aidat Tipi")
    
    # Hangi giderden kaynaklandığı (opsiyonel)
    gider = models.ForeignKey('Gider', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bağlı Gider")
    
    odendi_mi = models.BooleanField(default=False, verbose_name="Ödendi mi?")
    odeme_tarihi = models.DateField(null=True, blank=True, verbose_name="Ödeme Tarihi")
    kim_odedi = models.ForeignKey(Kisi, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ödeyen Kişi")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    gecikme_faizi = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Gecikme Faizi")
    
    def save(self, *args, **kwargs):
        # Eğer ödendi işaretlendiyse
        if self.pk:
            eski = Aidat.objects.get(pk=self.pk)
            if not eski.odendi_mi and self.odendi_mi:
                # Yeni ödendi - banka hareketi oluştur
                from .models import BankaHareket, Banka
                ana_hesap = Banka.objects.filter(ana_hesap_mi=True).first()
                if ana_hesap:
                    BankaHareket.objects.create(
                        banka=ana_hesap,
                        hareket_tipi='gelir',
                        tutar=self.tutar,
                        tarih=self.odeme_tarihi or date.today(),
                        aciklama=f"Aidat ödemesi - {self.daire} - {self.ay}/{self.yil}",
                        aidat=self,
                        kisi=self.kim_odedi
                    )
        super().save(*args, **kwargs)

    def __str__(self):
        tip = "🔹 Sabit" if self.aidat_tipi == 'sabit' else "📊 Ekstra"
        return f"{self.daire} - {self.ay}/{self.yil} - {self.tutar} TL {tip}"
    
    class Meta:
        verbose_name = "Aidat"
        verbose_name_plural = "Aidatlar"
        ordering = ['-yil', '-ay']
    
    @classmethod
    def aylik_sabit_aidatlari_olustur(cls, ay, yil):
        """Belirtilen ay ve yıl için tüm dairelere sabit aidat oluştur"""
        from .models import Daire, SiteAyarlari
        
        site_ayar = SiteAyarlari.objects.first()
        if not site_ayar or not site_ayar.sabit_aidat_aktif_mi:
            return
        
        sabit_tutar = site_ayar.sabit_aidat_miktari
        if sabit_tutar <= 0:
            return
        
        daireler = Daire.objects.all()
        olusturulan = 0
        guncellenen = 0
        
        for daire in daireler:
            aidat, created = cls.objects.get_or_create(
                daire=daire,
                ay=ay,
                yil=yil,
                aidat_tipi='sabit',
                defaults={
                    'tutar': sabit_tutar,
                    'aciklama': f"{ay}/{yil} Sabit Aidat"
                }
            )
            if created:
                olusturulan += 1
            else:
                if aidat.tutar != sabit_tutar:
                    aidat.tutar = sabit_tutar
                    aidat.save()
                    guncellenen += 1
        
        return {'olusturulan': olusturulan, 'guncellenen': guncellenen}

class Gider(models.Model):
    GIDER_TIPLERI = [
        ('elektrik', 'Elektrik'),
        ('su', 'Su'),
        ('dogalgaz', 'Yakıt / Doğalgaz'),
        ('yakıt', 'Yakıt/Kalorifer'),
        ('asansor', 'Asansör Bakım'),
        ('hidrofor', 'Hidrofor Bakım'),
        ('jenerator', 'Jeneratör Bakım'),
        ('yangin', 'Yangın Söndürme'),
        ('guvenlik', 'Güvenlik'),
        ('temizlik', 'Temizlik'),
        ('bahce', 'Bahçe Bakımı'),
        ('personel', 'Personel Maaşları'),
        ('sigorta', 'Sigorta'),
        ('vergi', 'Emlak Vergisi'),
        ('diger', 'Diğer'),
    ]
    
    GIDER_HESAP_TIPI = [
        ('esit', 'Eşit Bölüşüm (Ekstra Gider - Borç Olarak Yansır)'),
        ('hisse', 'Arsa Payına Göre (Ekstra Gider - Borç Olarak Yansır)'),
        ('brut_metrekare', 'Brüt Metrekareye Göre (Ekstra Gider - Borç Olarak Yansır)'),
        ('sabit_aidat', 'Sabit Aidat Kapsamında (Borç Yansıtma)'),
    ]
    
    # Temel bilgiler
    tip = models.CharField(max_length=20, choices=GIDER_TIPLERI, verbose_name="Gider Tipi")
    tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Toplam Tutar")
    tarih = models.DateField(default=date.today, verbose_name="Gider Tarihi")
    hesap_tipi = models.CharField(max_length=20, choices=GIDER_HESAP_TIPI, default='esit', verbose_name="Dağıtım Şekli")
    
    # İlişkiler (YENİ!)
    abonelik = models.ForeignKey('Abonelik', on_delete=models.SET_NULL, null=True, blank=True, 
                                 verbose_name="Abonelik", help_text="Elektrik/Su/Gaz aboneliği seçin")
    firma = models.ForeignKey('Firma', on_delete=models.SET_NULL, null=True, blank=True, 
                              verbose_name="Firma", help_text="Asansör/Hidrofor vb. firma seçin")
    
    # Fatura bilgileri
    fatura_no = models.CharField(max_length=50, blank=True, verbose_name="Fatura No")
    fatura_donemi = models.CharField(max_length=20, blank=True, verbose_name="Fatura Dönemi", 
                                     help_text="Örn: Mayıs 2026, 2026/1, Ocak-Şubat 2026")
    son_odeme_tarihi = models.DateField(null=True, blank=True, verbose_name="Son Ödeme Tarihi")
    odeme_tarihi = models.DateField(null=True, blank=True, verbose_name="Ödeme Tarihi")
    
    # Blok bazlı gider için (opsiyonel)
    blok = models.ForeignKey('Blok', on_delete=models.SET_NULL, null=True, blank=True, 
                            verbose_name="Blok", help_text="Sadece tek blokla ilgiliyse seçin")
    
    # Açıklama
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")

    def aidatlari_olustur(self):
        """Gidere göre dairelere aidat oluştur (yuvarlamalı)"""
        from decimal import Decimal, ROUND_HALF_UP
        from .models import Daire, Aidat, SiteAyarlari, Depozito, DepozitoHareket
        
        # Site ayarlarını al
        site_ayar = SiteAyarlari.objects.first()
        
        # Yakıt gideri mi kontrol et
        if self.tip in ['dogalgaz', 'yakıt']:
            aidat_tipi = 'yakıt'
        else:
            aidat_tipi = 'ekstra'
        
        daireler = Daire.objects.all()
        toplam_daire = daireler.count()
        
        # Toplam brüt metrekare
        toplam_brut = sum([d.brut_metrekare or 0 for d in daireler])
        if toplam_brut == 0:
            toplam_brut = 1
        
        # Toplam hisse
        toplam_hisse = sum([float(d.hisse_orani) for d in daireler])
        if toplam_hisse == 0:
            toplam_hisse = 1
        
        # Yuvarlama katı
        yuvarlama_kat = site_ayar.gider_yuvarlama_kat if site_ayar and site_ayar.gider_yuvarlama_aktif else 0
        yuvarlama_tip = site_ayar.gider_yuvarlama_tip if site_ayar else 'yukari'
        
        for daire in daireler:
            # Dağıtım şekline göre tutar hesapla
            if self.hesap_tipi == 'esit':
                tutar = self.tutar / toplam_daire
            elif self.hesap_tipi == 'brut_metrekare':
                oran = (daire.brut_metrekare or 0) / toplam_brut
                tutar = self.tutar * oran
            elif self.hesap_tipi == 'hisse':
                oran = float(daire.hisse_orani) / toplam_hisse
                tutar = self.tutar * oran
            else:
                tutar = 0
            
            # Yuvarlama işlemi
            orijinal_tutar = tutar
            if yuvarlama_kat > 0:
                if yuvarlama_tip == 'yukari':
                    yuvarlanan_tutar = math.ceil(tutar / yuvarlama_kat) * yuvarlama_kat
                elif yuvarlama_tip == 'asagi':
                    yuvarlanan_tutar = math.floor(tutar / yuvarlama_kat) * yuvarlama_kat
                else:  # en_yakin
                    yuvarlanan_tutar = round(tutar / yuvarlama_kat) * yuvarlama_kat
            else:
                yuvarlanan_tutar = tutar
            
            fark = yuvarlanan_tutar - tutar
            
            # Aidat oluştur
            ay = self.tarih.month
            yil = self.tarih.year
            
            aidat, created = Aidat.objects.get_or_create(
                daire=daire,
                ay=ay,
                yil=yil,
                aidat_tipi=aidat_tipi,
                gider=self,
                defaults={
                    'tutar': yuvarlanan_tutar,
                    'aciklama': f"{self.get_tip_display()} gideri - {self.tarih} (Yuvarlanmış: {orijinal_tutar:.2f} → {yuvarlanan_tutar:.2f})"
                }
            )
            if not created:
                aidat.tutar = yuvarlanan_tutar
                aidat.aciklama = f"{self.get_tip_display()} gideri - {self.tarih} (Yuvarlanmış: {orijinal_tutar:.2f} → {yuvarlanan_tutar:.2f})"
                aidat.save()
            
            # Farkı depozitoya ekle (artı olarak)
            if site_ayar and site_ayar.depozito_ekle and abs(fark) > 0.01:
                # Dairenin aktif depozitosunu bul
                depozito = Depozito.objects.filter(daire=daire, durum='alindi').first()
                if depozito:
                    DepozitoHareket.objects.create(
                        depozito=depozito,
                        hareket_tipi='ekleme' if fark > 0 else 'cikarma',
                        tutar=abs(fark),
                        tarih=self.tarih,
                        aciklama=f"{self.get_tip_display()} gider yuvarlama farkı (Borc: {orijinal_tutar:.2f} → Ödenen: {yuvarlanan_tutar:.2f})",
                        gider=self
                    )
                    print(f"{daire} depozitosuna {abs(fark):.2f} TL {'eklendi' if fark > 0 else 'eksildi'}")
    
    def __str__(self):
        if self.abonelik:
            return f"{self.get_tip_display()} - {self.abonelik} - {self.tutar} TL ({self.tarih})"
        elif self.firma:
            return f"{self.get_tip_display()} - {self.firma} - {self.tutar} TL ({self.tarih})"
        else:
            return f"{self.get_tip_display()} - {self.tutar} TL ({self.tarih})"
    
    class Meta:
        verbose_name = "Gider"
        verbose_name_plural = "Giderler"
        ordering = ['-tarih']

# ==================== SİTE TEMEL BİLGİLERİ ====================
class SiteAyarlari(models.Model):
    """Sitenin temel sabit bilgileri (sadece 1 kayıt)"""
    site_adi = models.CharField(max_length=200, verbose_name="Site Adı")
    adres = models.TextField(verbose_name="Adres")
    il = models.CharField(max_length=50, verbose_name="İl")
    ilce = models.CharField(max_length=50, verbose_name="İlçe")
    posta_kodu = models.CharField(max_length=10, blank=True, verbose_name="Posta Kodu")
    telefon = models.CharField(max_length=15, verbose_name="Site Telefonu")
    email = models.EmailField(verbose_name="Site E-posta")
    web_sitesi = models.URLField(blank=True, verbose_name="Web Sitesi")
    
    # Arsa Bilgileri
    toplam_arsa_m2 = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Toplam Arsa Alanı (m²)")
    toplam_brut_m2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Toplam Brüt Alan (m²)")
    
    # YENİ: Sabit Aidat Ayarları
    sabit_aidat_miktari = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                               verbose_name="Aylık Sabit Aidat (TL)")
    sabit_aidat_aktif_mi = models.BooleanField(default=True, 
                                                verbose_name="Sabit Aidat Aktif mi?")
    sabit_aidat_kesim_gunu = models.IntegerField(default=1, 
                                                  verbose_name="Sabit Aidat Kesim Günü")
    
    # Ayarlar
    aidat_hesap_gunu = models.IntegerField(default=1, verbose_name="Aidat Kesim Günü")
    gecikme_faizi_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Gecikme Faizi Oranı (%)")
    
    # Yuvarlama Ayarları
    YUVARLAMA_TIPI = [
        ('yukari', 'Yukarı Yuvarla'),
        ('asagi', 'Aşağı Yuvarla'),
        ('en_yakin', 'En Yakına Yuvarla'),
    ]
    
    gider_yuvarlama_aktif = models.BooleanField(default=False, verbose_name="Gider Yuvarlama Aktif")
    gider_yuvarlama_tip = models.CharField(max_length=10, choices=YUVARLAMA_TIPI, default='yukari', verbose_name="Yuvarlama Tipi")
    gider_yuvarlama_kat = models.IntegerField(default=10, verbose_name="Yuvarlama Katı (TL)", help_text="10, 50, 100 TL gibi")
    depozito_ekle = models.BooleanField(default=True, verbose_name="Kalan Tutarı Depozitoya Ekle")

    # Açıklama
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    def __str__(self):
        return self.site_adi
    
    def save(self, *args, **kwargs):
        # Sadece bir kayıt olmasını sağla
        if not self.pk and SiteAyarlari.objects.exists():
            raise ValueError("Sadece bir Site Ayarı kaydı olabilir!")
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Site Ayarı"
        verbose_name_plural = "Site Ayarları"


# ==================== YÖNETİCİLER ====================
class Yonetici(models.Model):
    YONETICI_TIPI = [
        ('baskan', 'Yönetim Kurulu Başkanı'),
        ('baskan_yrd', 'Başkan Yardımcısı'),
        ('uyeler', 'Yönetim Kurulu Üyesi'),
        ('denetci', 'Denetçi'),
        ('sekreter', 'Sekreter'),
        ('sayman', 'Sayman'),
        ('diger', 'Diğer'),
    ]
    
    ad_soyad = models.CharField(max_length=100, verbose_name="Ad Soyad")
    gorev_tipi = models.CharField(max_length=20, choices=YONETICI_TIPI, verbose_name="Görev Tipi")
    telefon = models.CharField(max_length=15, verbose_name="Telefon")
    email = models.EmailField(verbose_name="E-posta")
    gorev_baslangic = models.DateField(verbose_name="Görev Başlangıç Tarihi")
    gorev_bitis = models.DateField(null=True, blank=True, verbose_name="Görev Bitiş Tarihi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    def __str__(self):
        return f"{self.ad_soyad} ({self.get_gorev_tipi_display()})"
    
    class Meta:
        verbose_name = "Yönetici"
        verbose_name_plural = "Yöneticiler"
        ordering = ['gorev_baslangic']


# ==================== ABONELİKLER ====================
class Abonelik(models.Model):
    ABONELIK_TIPI = [
        ('elektrik', 'Elektrik'),
        ('su', 'Su'),
        ('dogalgaz', 'Doğalgaz'),
        ('internet', 'İnternet'),
        ('telefon', 'Telefon'),
        ('kablo_tv', 'Kablo TV'),
        ('diger', 'Diğer'),
    ]
    
    tip = models.CharField(max_length=20, choices=ABONELIK_TIPI, verbose_name="Abonelik Tipi")
    firma_adi = models.CharField(max_length=100, verbose_name="Firma Adı")
    abone_no = models.CharField(max_length=50, verbose_name="Abone No")
    abone_adi = models.CharField(max_length=100, verbose_name="Abone Adı")
    telefon = models.CharField(max_length=15, blank=True, verbose_name="İrtibat Telefonu")
    
    # Aboneliğin bağlı olduğu blok (opsiyonel)
    blok = models.ForeignKey('Blok', on_delete=models.SET_NULL, null=True, blank=True, 
                            verbose_name="Bağlı Blok", help_text="Sadece tek bloğa aitse seçin")
    
    # Fatura bilgileri
    son_fatura_tarihi = models.DateField(null=True, blank=True, verbose_name="Son Fatura Tarihi")
    ortalama_tutar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                         verbose_name="Ortalama Aylık Tutar")
    
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    def __str__(self):
        blok_info = f" ({self.blok})" if self.blok else ""
        return f"{self.get_tip_display()} - {self.firma_adi} ({self.abone_no}){blok_info}"
    
    class Meta:
        verbose_name = "Abonelik"
        verbose_name_plural = "Abonelikler"


# ==================== FİRMALAR (Asansör, Hidrofor vb.) ====================
class Firma(models.Model):
    FIRMA_TIPI = [
        ('asansor', 'Asansör Bakım'),
        ('hidrofor', 'Hidrofor Bakım'),
        ('jenerator', 'Jeneratör Bakım'),
        ('yangin', 'Yangın Söndürme'),
        ('peyzaj', 'Peyzaj'),
        ('temizlik', 'Temizlik Şirketi'),
        ('guvenlik', 'Güvenlik Şirketi'),
        ('teknik_servis', 'Teknik Servis'),
        ('diger', 'Diğer'),
    ]
    
    tip = models.CharField(max_length=20, choices=FIRMA_TIPI, verbose_name="Firma Tipi")
    firma_adi = models.CharField(max_length=100, verbose_name="Firma Adı")
    yetkili_kisi = models.CharField(max_length=100, verbose_name="Yetkili Kişi")
    telefon = models.CharField(max_length=15, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="E-posta")
    adres = models.TextField(blank=True, verbose_name="Adres")
    
    # Sözleşme bilgileri
    sozlesme_no = models.CharField(max_length=50, blank=True, verbose_name="Sözleşme No")
    sozlesme_baslangic = models.DateField(verbose_name="Sözleşme Başlangıç")
    sozlesme_bitis = models.DateField(verbose_name="Sözleşme Bitiş")
    aylik_ucret = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                      verbose_name="Aylık Ücret (TL)")
    
    # Periyodik bakım bilgileri
    bakim_periyodu = models.CharField(max_length=50, blank=True, verbose_name="Bakım Periyodu", 
                                      help_text="Örn: Aylık, 3 ayda bir, Yıllık")
    son_bakim_tarihi = models.DateField(null=True, blank=True, verbose_name="Son Bakım Tarihi")
    sonraki_bakim_tarihi = models.DateField(null=True, blank=True, verbose_name="Sonraki Bakım Tarihi")
    
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    def __str__(self):
        return f"{self.get_tip_display()} - {self.firma_adi}"
    
    class Meta:
        verbose_name = "Firma"
        verbose_name_plural = "Firmalar"


# ==================== BANKA HESAPLARI ====================
class Banka(models.Model):
    """Banka hesapları ve nakit/bono gibi varlıklar"""
    HESAP_TIPI = [
        ('vadesiz', 'Vadesiz Hesap'),
        ('vadeli', 'Vadeli Hesap'),
        ('nakit', 'Nakit Kasa'),
        ('bono', 'Bono'),
        ('cek', 'Çek'),
        ('diger', 'Diğer'),
    ]
    
    # Banka Bilgileri
    banka_adi = models.CharField(max_length=100, verbose_name="Banka Adı")
    sube_adi = models.CharField(max_length=100, verbose_name="Şube Adı")
    sube_kodu = models.CharField(max_length=10, verbose_name="Şube Kodu")
    hesap_adi = models.CharField(max_length=100, verbose_name="Hesap Adı")
    hesap_no = models.CharField(max_length=20, verbose_name="Hesap No")
    iban = models.CharField(max_length=34, blank=True, verbose_name="IBAN")
    hesap_tipi = models.CharField(max_length=20, choices=HESAP_TIPI, default='vadesiz', verbose_name="Hesap Tipi")
    
    # Bakiye Bilgileri
    acilis_bakiyesi = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Açılış Bakiyesi (TL)")
    guncel_bakiye = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Güncel Bakiye (TL)")
    bloke_bakiye = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Bloke Bakiye (TL)")
    
    # Yetkililer
    yetkili_kisi = models.CharField(max_length=100, blank=True, verbose_name="Yetkili Kişi")
    ikinci_yetkili = models.CharField(max_length=100, blank=True, verbose_name="İkinci Yetkili")
    
    # Durum
    ana_hesap_mi = models.BooleanField(default=False, verbose_name="Ana Hesap mı?")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    def __str__(self):
        if self.hesap_tipi in ['nakit', 'bono', 'cek']:
            return f"{self.get_hesap_tipi_display()} - {self.hesap_adi} ({self.guncel_bakiye} TL)"
        return f"{self.banka_adi} - {self.hesap_adi} ({self.hesap_no})"
    
    class Meta:
        verbose_name = "Banka/Nakit Hesap"
        verbose_name_plural = "Bankalar ve Nakit Hesapları"


class BankaHareket(models.Model):
    """Banka hesabındaki para giriş/çıkış hareketleri"""
    HAREKET_TIPI = [
        ('gelir', 'Gelir'),
        ('gider', 'Gider'),
        ('transfer', 'Transfer'),
    ]
    
    banka = models.ForeignKey(Banka, on_delete=models.CASCADE, verbose_name="Hesap", related_name='hareketler')
    hareket_tipi = models.CharField(max_length=20, choices=HAREKET_TIPI, verbose_name="Hareket Tipi")
    tutar = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Tutar (TL)")
    tarih = models.DateField(default=date.today, verbose_name="İşlem Tarihi")
    aciklama = models.TextField(verbose_name="Açıklama")
    
    # İlişkili kayıtlar (opsiyonel)
    aidat = models.ForeignKey('Aidat', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlişkili Aidat")
    gider = models.ForeignKey('Gider', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlişkili Gider")
    depozito = models.ForeignKey('Depozito', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlişkili Depozito")  # YENİ EKLE
    kisi = models.ForeignKey('Kisi', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlişkili Kişi")
    
    # Dekont/Fatura
    dekont_no = models.CharField(max_length=50, blank=True, verbose_name="Dekont/Fatura No")
    
    def save(self, *args, **kwargs):
        # Hesap bakiyesini güncelle (sinyal yerine burada yapalım)
        if self.pk is None:  # Yeni kayıt
            if self.hareket_tipi == 'gelir':
                self.banka.guncel_bakiye += self.tutar
            elif self.hareket_tipi == 'gider':
                self.banka.guncel_bakiye -= self.tutar
            self.banka.save()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.banka} - {self.get_hareket_tipi_display()} - {self.tutar} TL ({self.tarih})"
    
    class Meta:
        verbose_name = "Banka Hareketi"
        verbose_name_plural = "Banka Hareketleri"
        ordering = ['-tarih']


class Depozito(models.Model):
    """Kat maliklerinden alınan depozito yönetimi"""
    DURUM = [
        ('alindi', 'Alındı'),
        ('iade_edildi', 'İade Edildi'),
        ('mahsup', 'Mahsup Edildi'),
    ]
    
    daire = models.ForeignKey(Daire, on_delete=models.CASCADE, verbose_name="Daire", related_name='depozitolar')
    kisi = models.ForeignKey(Kisi, on_delete=models.CASCADE, verbose_name="Depozito Veren")  # limit_choices_to kaldırıldı
    tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Depozito Tutarı (TL)")
    alinma_tarihi = models.DateField(default=date.today, verbose_name="Alınma Tarihi")
    durum = models.CharField(max_length=20, choices=DURUM, default='alindi', verbose_name="Durum")
    iade_tarihi = models.DateField(null=True, blank=True, verbose_name="İade Tarihi")
    iade_tutari = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="İade Tutarı")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    
    # Hangi hesaba yatırıldığı
    banka = models.ForeignKey('Banka', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Yatırılan Hesap")
    
    def kalan_bakiye(self):
        """Kalan depozito miktarı"""
        if self.durum == 'alindi':
            return float(self.tutar)
        return 0
    
    def __str__(self):
        return f"{self.daire} - {self.kisi} - {self.tutar} TL ({self.get_durum_display()})"
    
    class Meta:
        verbose_name = "Depozito"
        verbose_name_plural = "Depozitolar"


class DepozitoHareket(models.Model):
    """Depozitoya yapılan ekleme/çıkarma hareketleri (yuvarlama fazlalıkları vb.)"""
    HAREKET_TIPI = [
        ('ekleme', 'Ekleme (Fazla Ödeme)'),
        ('cikarma', 'Çıkarma (Mahsup)'),
        ('iade', 'İade'),
    ]
    
    depozito = models.ForeignKey(Depozito, on_delete=models.CASCADE, verbose_name="Depozito", related_name='hareketler')
    hareket_tipi = models.CharField(max_length=20, choices=HAREKET_TIPI, verbose_name="Hareket Tipi")
    tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tutar")
    tarih = models.DateField(default=date.today, verbose_name="İşlem Tarihi")
    aciklama = models.TextField(verbose_name="Açıklama")
    
    # Bağlı olduğu gider (yakıt hesaplamasındaki yuvarlama için)
    gider = models.ForeignKey('Gider', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Bağlı Gider")
    
    def __str__(self):
        return f"{self.depozito.daire} - {self.get_hareket_tipi_display()} - {self.tutar} TL"
    
    class Meta:
        verbose_name = "Depozito Hareketi"
        verbose_name_plural = "Depozito Hareketleri"

from django.db.models.signals import post_save
from django.dispatch import receiver

# ==================== SİNYALLER (Otomatik Hesap Hareketleri) ====================

@receiver(post_save, sender=Aidat)
def aidat_odeme_banka_hareketi(sender, instance, created, **kwargs):
    """Aidat ödendiğinde banka hareketi oluştur"""
    if instance.odendi_mi and instance.odeme_tarihi and instance.tutar > 0:
        # Daha önce hareket oluşmuş mu kontrol et
        existing = BankaHareket.objects.filter(aidat=instance).first()
        if not existing:
            ana_hesap = Banka.objects.filter(ana_hesap_mi=True).first()
            if ana_hesap:
                BankaHareket.objects.create(
                    banka=ana_hesap,
                    hareket_tipi='gelir',
                    tutar=instance.tutar,
                    tarih=instance.odeme_tarihi,
                    aciklama=f"Aidat ödemesi - {instance.daire} - {instance.ay}/{instance.yil}",
                    aidat=instance,
                    kisi=instance.kim_odedi
                )

@receiver(post_save, sender=Gider)
def gider_banka_hareketi(sender, instance, created, **kwargs):
    """Gider ödendiğinde banka hareketi oluştur"""
    if instance.odeme_tarihi and instance.tutar > 0:
        existing = BankaHareket.objects.filter(gider=instance).first()
        if not existing:
            ana_hesap = Banka.objects.filter(ana_hesap_mi=True).first()
            if ana_hesap:
                BankaHareket.objects.create(
                    banka=ana_hesap,
                    hareket_tipi='gider',
                    tutar=instance.tutar,
                    tarih=instance.odeme_tarihi,
                    aciklama=f"Gider ödemesi - {instance.get_tip_display()} - {instance.tarih}",
                    gider=instance
                )

@receiver(post_save, sender=Depozito)
def depozito_banka_hareketi(sender, instance, created, **kwargs):
    """Depozito alındığında/iade edildiğinde banka hareketi oluştur"""
    if instance.durum == 'alindi' and instance.banka and instance.tutar > 0:
        existing = BankaHareket.objects.filter(depozito=instance, hareket_tipi='gelir').first()
        if not existing:
            BankaHareket.objects.create(
                banka=instance.banka,
                hareket_tipi='gelir',
                tutar=instance.tutar,
                tarih=instance.alinma_tarihi,
                aciklama=f"Depozito alındı - {instance.daire} - {instance.kisi}",
                depozito=instance,
                kisi=instance.kisi
            )
    elif instance.durum == 'iade_edildi' and instance.iade_tutari and instance.banka:
        existing = BankaHareket.objects.filter(depozito=instance, hareket_tipi='gider').first()
        if not existing:
            BankaHareket.objects.create(
                banka=instance.banka,
                hareket_tipi='gider',
                tutar=instance.iade_tutari,
                tarih=instance.iade_tarihi or date.today(),
                aciklama=f"Depozito iadesi - {instance.daire} - {instance.kisi}",
                depozito=instance,
                kisi=instance.kisi
            )

class Fatura(models.Model):
    """Fatura/dekont dosyaları"""
    FATURA_TIPI = [
        ('elektrik', 'Elektrik'),
        ('su', 'Su'),
        ('dogalgaz', 'Doğalgaz'),
        ('aidat', 'Aidat'),
        ('depozito', 'Depozito'),
        ('diger', 'Diğer'),
    ]
    
    tip = models.CharField(max_length=20, choices=FATURA_TIPI, verbose_name="Fatura Tipi")
    dosya = models.FileField(upload_to='faturalar/%Y/%m/', verbose_name="Fatura Dosyası")
    aciklama = models.CharField(max_length=200, verbose_name="Açıklama")
    tarih = models.DateField(default=date.today, verbose_name="Yükleme Tarihi")
    
    # İlişkili kayıtlar
    aidat = models.ForeignKey('Aidat', on_delete=models.SET_NULL, null=True, blank=True)
    gider = models.ForeignKey('Gider', on_delete=models.SET_NULL, null=True, blank=True)
    depozito = models.ForeignKey('Depozito', on_delete=models.SET_NULL, null=True, blank=True)
    banka_hareket = models.ForeignKey('BankaHareket', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_tip_display()} - {self.aciklama}"
    
    class Meta:
        verbose_name = "Fatura/Dekont"
        verbose_name_plural = "Faturalar/Dekontlar"

class Fatura(models.Model):
    """Fatura/dekont dosyaları"""
    FATURA_TIPI = [
        ('elektrik', 'Elektrik'),
        ('su', 'Su'),
        ('dogalgaz', 'Doğalgaz'),
        ('aidat', 'Aidat'),
        ('depozito', 'Depozito'),
        ('diger', 'Diğer'),
    ]
    
    tip = models.CharField(max_length=20, choices=FATURA_TIPI, verbose_name="Fatura Tipi")
    dosya = models.FileField(upload_to='faturalar/%Y/%m/', verbose_name="Fatura Dosyası")
    aciklama = models.CharField(max_length=200, verbose_name="Açıklama")
    tarih = models.DateField(default=date.today, verbose_name="Yükleme Tarihi")
    
    # İlişkili kayıtlar
    aidat = models.ForeignKey('Aidat', on_delete=models.SET_NULL, null=True, blank=True)
    gider = models.ForeignKey('Gider', on_delete=models.SET_NULL, null=True, blank=True)
    depozito = models.ForeignKey('Depozito', on_delete=models.SET_NULL, null=True, blank=True)
    banka_hareket = models.ForeignKey('BankaHareket', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_tip_display()} - {self.aciklama}"
    
    class Meta:
        verbose_name = "Fatura/Dekont"
        verbose_name_plural = "Faturalar/Dekontlar"

# ==================== PERSONEL / MAAŞ MODÜLÜ ====================

class Personel(models.Model):
    """Personel bilgileri"""
    CALISMA_SEKLI = [
        ('tam_zamanli', 'Tam Zamanlı'),
        ('yarim_zamanli', 'Yarı Zamanlı'),
        ('sozlesmeli', 'Sözleşmeli'),
        ('mevsimlik', 'Mevsimlik'),
    ]
    
    SGK_TIPI = [
        ('normal', 'Normal (%14)'),
        ('engelli', 'Engelli (%12)'),
        ('yuzde40', '%40 İndirimli'),
    ]

    MAAŞ_TIPI = [
        ('brut', 'Brüt Maaş'),
        ('net', 'Net Maaş'),
    ]
    
    maas_tipi = models.CharField(max_length=10, choices=MAAŞ_TIPI, default='brut', verbose_name="Maaş Tipi")
    
    ad_soyad = models.CharField(max_length=100, verbose_name="Ad Soyad")
    tc_kimlik = models.CharField(max_length=11, unique=True, verbose_name="TC Kimlik No")
    unvan = models.CharField(max_length=100, blank=True, verbose_name="Ünvan / Görev")
    ise_baslama_tarihi = models.DateField(verbose_name="İşe Başlama Tarihi")
    isten_cikis_tarihi = models.DateField(null=True, blank=True, verbose_name="İşten Çıkış Tarihi")
    calisma_sekli = models.CharField(max_length=20, choices=CALISMA_SEKLI, default='tam_zamanli', verbose_name="Çalışma Şekli")
    sgk_tipi = models.CharField(max_length=20, choices=SGK_TIPI, default='normal', verbose_name="SGK Tipi")
    brut_maas = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    verbose_name="Maaş (TL)", 
    help_text="⚠️ DİKKAT: Maaş Tipi 'Brüt' seçildiyse BRÜT ücret (Örn: 33030), 'Net' seçildiyse NET ücret (Örn: 28075) yazınız.")
    tesvik_durumu = models.BooleanField(default=False, verbose_name="5 Puanlık SGK Teşviki", help_text="İmalat sektörü için 5 puan indirim")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    def __str__(self):
        return f"{self.ad_soyad} - {self.unvan}"
    
    class Meta:
        verbose_name = "Personel"
        verbose_name_plural = "Personeller"
        ordering = ['ad_soyad']


class AsgariUcret(models.Model):
    """Asgari ücret parametreleri (her yıl güncellenir)"""
    yil = models.IntegerField(unique=True, verbose_name="Yıl")
    brut_ucret = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Brüt Asgari Ücret (TL)")
    isci_sgk_payi = models.DecimalField(max_digits=5, decimal_places=2, default=14.00, verbose_name="İşçi SGK Payı (%)")
    isci_issizlik_payi = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, verbose_name="İşçi İşsizlik Payı (%)")
    isveren_sgk_payi = models.DecimalField(max_digits=5, decimal_places=2, default=20.75, verbose_name="İşveren SGK Payı (%)")
    isveren_issizlik_payi = models.DecimalField(max_digits=5, decimal_places=2, default=2.00, verbose_name="İşveren İşsizlik Payı (%)")
    tesvik_orani = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, verbose_name="Teşvik Oranı (%)")
    
    def __str__(self):
        return f"{self.yil} - {self.brut_ucret} TL"
    
    class Meta:
        verbose_name = "Asgari Ücret"
        verbose_name_plural = "Asgari Ücretler"


class MaasBordrosu(models.Model):
    """Aylık maaş bordroları"""
    personel = models.ForeignKey(Personel, on_delete=models.CASCADE, related_name='bordrolar', verbose_name="Personel")
    ay = models.IntegerField(verbose_name="Ay")
    yil = models.IntegerField(verbose_name="Yıl")
    brut_maas = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Brüt Maaş")
    
    # NET MAAŞ GİRİŞ ALANI (Personel Net seçtiyse kullanılacak)
    girilen_net_maas = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Net Maaş (TL)")
    
    # EK ÖDEMELER (Girilen değerler)
    fazla_mesai_saati = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Fazla Mesai (Saat)")
    resmi_tatil_gun = models.IntegerField(default=0, verbose_name="Resmi Tatil (Gün)")
    bayram_gun = models.IntegerField(default=0, verbose_name="Bayram (Gün)")
    prim = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Prim/İkramiye (TL)")
    
    # HESAPLANAN EK ÖDEMELER (YENİ - Otomatik doldurulacak)
    fazla_mesai_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Fazla Mesai Tutarı (TL)")
    resmi_tatil_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Resmi Tatil Tutarı (TL)")
    bayram_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Bayram Tutarı (TL)")
    
    # Kesintiler
    sgk_isci_payi = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="SGK İşçi Payı")
    issizlik_isci_payi = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="İşsizlik İşçi Payı")
    gelir_vergisi = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Gelir Vergisi")
    damga_vergisi = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Damga Vergisi")
    toplam_kesinti = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Toplam Kesinti")
    
    # Net
    net_maas = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Net Maaş")
    
    # İşveren maliyeti
    sgk_isveren_payi = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="SGK İşveren Payı")
    issizlik_isveren_payi = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="İşsizlik İşveren Payı")
    isveren_toplam_maliyet = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="İşveren Toplam Maliyet")

    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    
    class Meta:
        unique_together = ['personel', 'yil', 'ay']
        ordering = ['-yil', '-ay', 'personel__ad_soyad']
        verbose_name = "Maaş Bordrosu"
        verbose_name_plural = "Maaş Bordroları"
    
    def get_ay_display(self):
        aylar = {
            1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
            5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
            9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
        }
        return aylar.get(self.ay, '')
    
    def __str__(self):
        aylar = ['', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        return f"{self.personel.ad_soyad} - {aylar[self.ay]} {self.yil}"