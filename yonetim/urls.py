from django.urls import path
from . import views

urlpatterns = [
    path('', views.ana_sayfa, name='ana_sayfa'),
    path('bloklar/', views.blok_listesi, name='blok_listesi'),
    path('blok/ekle/', views.blok_ekle, name='blok_ekle'),
    path('blok/<int:blok_id>/', views.blok_detay, name='blok_detay'),
    path('blok/<int:blok_id>/daire-ekle/', views.daire_ekle, name='blok_daire_ekle'),
    path('daire-ekle/', views.daire_ekle, name='daire_ekle'),
    path('kisiler/', views.kisi_listesi, name='kisi_listesi'),
    path('kisi/ekle/', views.kisi_ekle, name='kisi_ekle'),
    path('daire-iliski/ekle/', views.daire_iliski_ekle, name='daire_iliski_ekle'),
    path('daire-iliski/ekle/<int:kisi_id>/', views.daire_iliski_ekle, name='daire_iliski_ekle_kisi'),
    path('aidatlar/', views.aidat_listesi, name='aidat_listesi'),
    path('aidat/ekle/', views.aidat_ekle, name='aidat_ekle'),
    
    # RAPORLAR
    path('rapor/<int:yil>/<int:ay>/', views.aidat_raporu, name='aidat_raporu'),
    path('rapor/', views.aidat_raporu, name='aidat_raporu_current'),
]