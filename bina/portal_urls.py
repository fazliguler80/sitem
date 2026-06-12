# bina/portal_urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import portal_views

urlpatterns = [
    # Giriş/Çıkış
    path('login/', portal_views.portal_login, name='portal_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/portal/login/'), name='portal_logout'),
    
    # Ana Sayfa
    path('', portal_views.portal_ana_sayfa, name='portal_ana'),
    
    # DEPOZİTO SAYFALARI (YENİ)
    path('depozito/', portal_views.depozito_gecmisi, name='depozito_gecmisi'),
    path('depozito/<int:depozito_id>/', portal_views.depozito_detay, name='depozito_detay'),
    
    # Aidat ve Borç
    path('aidat/', portal_views.aidat_gecmisi, name='aidat_gecmisi'),
    path('borc/', portal_views.borc_durumu, name='borc_durumu'),
    
    # Komşular
    path('komsular/', portal_views.komsular, name='komsular'),
    path('komsular/<str:blok>/', portal_views.komsular, name='komsular_blok'),
    
    # Profil
    path('profil/', portal_views.profil_duzenle, name='profil_duzenle'),
    
    # Şifre sıfırlama
    path('sifre-sifirla/<uidb64>/<token>/', portal_views.sifre_sifirla_confirm, name='sifre_sifirla_confirm'),
    path('sifre-degistir-zorunlu/', portal_views.sifre_degistir_zorunlu, name='sifre_degistir_zorunlu'),
]