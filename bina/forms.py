from django import forms
from .models import Blok, Daire, Kisi, DaireIliskisi, Aidat, Gider, SiteAyarlari

class SiteAyarlariForm(forms.ModelForm):
    class Meta:
        model = SiteAyarlari
        fields = '__all__'
        widgets = {
            'site_adi': forms.TextInput(attrs={'class': 'form-control'}),
            'adres': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'il': forms.TextInput(attrs={'class': 'form-control'}),
            'ilce': forms.TextInput(attrs={'class': 'form-control'}),
            'posta_kodu': forms.TextInput(attrs={'class': 'form-control'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'toplam_arsa_m2': forms.NumberInput(attrs={'class': 'form-control'}),
            'elektrik_abone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'su_abone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'dogalgaz_abone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'apartman_gorevlisi': forms.TextInput(attrs={'class': 'form-control'}),
            'guvenlik_gorevlisi': forms.TextInput(attrs={'class': 'form-control'}),
            'bahcivan': forms.TextInput(attrs={'class': 'form-control'}),
            'banka_adi': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'hesap_sahibi': forms.TextInput(attrs={'class': 'form-control'}),
            'yonetim_kurulu_baskani': forms.TextInput(attrs={'class': 'form-control'}),
            'yonetim_kurulu_uyeleri': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'denetci': forms.TextInput(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BlokForm(forms.ModelForm):
    class Meta:
        model = Blok
        fields = ['blok_adi', 'kat_sayisi', 'daire_sayisi']
        widgets = {
            'blok_adi': forms.Select(attrs={'class': 'form-control'}),
            'kat_sayisi': forms.NumberInput(attrs={'class': 'form-control'}),
            'daire_sayisi': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class MaasBordrosuForm(forms.ModelForm):
    net_maas_hesapla = forms.DecimalField(
        required=False, 
        label="Net Maaş Gir (TL)",
        help_text="Buraya net maaş yazarsanız brüt otomatik hesaplanır",
        decimal_places=2
    )

class DaireForm(forms.ModelForm):
    class Meta:
        model = Daire
        fields = [
            'daire_no', 'daire_tipi', 'tasinmaz_tipi', 'nitelik',
            'kat', 'net_metrekare', 'brut_metrekare', 'balkon_m2', 'oda_sayisi',
            'arsa_pay_pay', 'arsa_pay_payda',
            'tapu_kayit_no', 'tapu_sahibi', 'tapu_tarihi'
        ]
        widgets = {
            'daire_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 1, 2, 3A'}),
            'daire_tipi': forms.Select(attrs={'class': 'form-control'}),
            'tasinmaz_tipi': forms.Select(attrs={'class': 'form-control'}),
            'nitelik': forms.Select(attrs={'class': 'form-control'}),
            'kat': forms.NumberInput(attrs={'class': 'form-control'}),
            'net_metrekare': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 135'}),
            'brut_metrekare': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 150'}),
            'balkon_m2': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 10'}),
            'oda_sayisi': forms.NumberInput(attrs={'class': 'form-control'}),
            'arsa_pay_pay': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 48'}),
            'arsa_pay_payda': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 2700'}),
            'tapu_kayit_no': forms.TextInput(attrs={'class': 'form-control'}),
            'tapu_sahibi': forms.TextInput(attrs={'class': 'form-control'}),
            'tapu_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        help_texts = {
            'net_metrekare': 'Dairenin iç net alanı (m²) - Örn: 135',
            'brut_metrekare': 'Duvarlar dahil toplam alan (m²) - YAKIT HESABI İÇİN - Örn: 150',
            'arsa_pay_pay': 'Arsa payının pay kısmı - Örn: 48 (48/2700 için)',
            'arsa_pay_payda': 'Arsa payının payda kısmı - Örn: 2700 (48/2700 için)',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        arsa_pay_pay = cleaned_data.get('arsa_pay_pay')
        arsa_pay_payda = cleaned_data.get('arsa_pay_payda')
        
        if arsa_pay_pay and arsa_pay_payda:
            if arsa_pay_pay > arsa_pay_payda:
                raise forms.ValidationError("Arsa payı (pay), paydadan büyük olamaz!")
            if arsa_pay_pay <= 0 or arsa_pay_payda <= 0:
                raise forms.ValidationError("Arsa payı değerleri pozitif olmalıdır!")
        
        brut = cleaned_data.get('brut_metrekare')
        net = cleaned_data.get('net_metrekare')
        
        if brut and net and brut < net:
            raise forms.ValidationError("Brüt metrekare, net metrekareden küçük olamaz!")
        
        return cleaned_data


class KisiForm(forms.ModelForm):
    class Meta:
        model = Kisi
        fields = ['ad_soyad', 'kisi_tipi', 'tc_kimlik', 'telefon', 'email', 'adres']
        widgets = {
            'ad_soyad': forms.TextInput(attrs={'class': 'form-control'}),
            'kisi_tipi': forms.Select(attrs={'class': 'form-control'}),
            'tc_kimlik': forms.TextInput(attrs={'class': 'form-control'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adres': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DaireIliskisiForm(forms.ModelForm):
    class Meta:
        model = DaireIliskisi
        fields = ['daire', 'kisi', 'iliski_tipi', 'baslangic_tarihi']
        widgets = {
            'daire': forms.Select(attrs={'class': 'form-control'}),
            'kisi': forms.Select(attrs={'class': 'form-control'}),
            'iliski_tipi': forms.Select(attrs={'class': 'form-control'}),
            'baslangic_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class AidatForm(forms.ModelForm):
    class Meta:
        model = Aidat
        fields = ['daire', 'ay', 'yil', 'tutar', 'aciklama']
        widgets = {
            'daire': forms.Select(attrs={'class': 'form-control'}),
            'ay': forms.Select(attrs={'class': 'form-control'}),
            'yil': forms.NumberInput(attrs={'class': 'form-control'}),
            'tutar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ay seçenekleri
        aylar = [
            ('Ocak', 'Ocak'), ('Şubat', 'Şubat'), ('Mart', 'Mart'),
            ('Nisan', 'Nisan'), ('Mayıs', 'Mayıs'), ('Haziran', 'Haziran'),
            ('Temmuz', 'Temmuz'), ('Ağustos', 'Ağustos'), ('Eylül', 'Eylül'),
            ('Ekim', 'Ekim'), ('Kasım', 'Kasım'), ('Aralık', 'Aralık')
        ]
        self.fields['ay'].choices = aylar