from django.urls import path
from django.contrib.auth import views as auth_views
from . import portal_views

urlpatterns = [
    path('login/', portal_views.portal_login, name='portal_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/portal/login/'), name='portal_logout'),
    path('', portal_views.portal_ana_sayfa, name='portal_ana'),
    path('aidat/', portal_views.aidat_gecmisi, name='aidat_gecmisi'),
    path('borc/', portal_views.borc_durumu, name='borc_durumu'),
    path('komsular/', portal_views.komsular, name='komsular'),
    path('komsular/<str:blok>/', portal_views.komsular, name='komsular_blok'),
    path('profil/', portal_views.profil_duzenle, name='profil_duzenle'),
    
    # Şifre sıfırlama (SADECE BİR TANE OLMALI - MANUEL OLAN)
    path('sifre-sifirla/<uidb64>/<token>/', portal_views.sifre_sifirla_confirm, name='sifre_sifirla_confirm'),
]