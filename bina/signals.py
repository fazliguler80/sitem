# bina/signals.py
from django.db.models.signals import pre_delete, post_delete, post_save
from django.dispatch import receiver
from .models import Gider, Aidat, DepozitoHareket, Depozito, BankaHareket, Banka
from decimal import Decimal
from datetime import date


@receiver(pre_delete, sender=Gider)
def gider_silinmeden_once_aidatlari_sil(sender, instance, **kwargs):
    """Gider silinmeden önce bağlı aidatları ve depozito hareketlerini sil"""
    print(f"\n=== Gider siliniyor: {instance} ===")
    
    aidatlar = Aidat.objects.filter(gider=instance)
    aidat_sayisi = aidatlar.count()
    
    if aidat_sayisi > 0:
        print(f"  {aidat_sayisi} adet aidat siliniyor...")
        for aidat in aidatlar:
            print(f"    - {aidat.daire} - {aidat.ay}/{aidat.yil} - {aidat.tutar} TL")
            aidat.delete()
        print(f"  ✅ {aidat_sayisi} aidat silindi.")
    else:
        print("  Bağlı aidat bulunamadı.")
    
    depozito_hareketleri = DepozitoHareket.objects.filter(gider=instance)
    depozito_sayisi = depozito_hareketleri.count()
    
    if depozito_sayisi > 0:
        print(f"  {depozito_sayisi} adet depozito hareketi siliniyor...")
        for hareket in depozito_hareketleri:
            print(f"    - {hareket.depozito.daire} - {hareket.tutar} TL - {hareket.aciklama}")
            hareket.delete()
        print(f"  ✅ {depozito_sayisi} depozito hareketi silindi.")
    
    print(f"=== Gider silme işlemi tamamlandı ===\n")


@receiver(post_delete, sender=Gider)
def gider_silindikten_sonra_mesaj(sender, instance, **kwargs):
    """Gider silindikten sonra bilgi mesajı"""
    print(f"Gider başarıyla silindi: {instance}")


#@receiver(post_save, sender=Aidat)
#def aidat_odeme_sonrasi_depozito(sender, instance, created, **kwargs):
#    """
 #   Aidat ödeme durumu değiştiğinde (ödendi veya iptal) depozito hareketini yönetir.
  #  """
    # Eğer yeni kayıt değilse (güncelleme ise)
   # if not created:
    #    try:
     #       eski = Aidat.objects.get(pk=instance.pk)
      #      # Ödeme durumu değişti mi?
       #     if eski.odeme_yapildi_mi != instance.odeme_yapildi_mi:
        #        if instance.odeme_yapildi_mi:
         #           # Ödeme yapıldıysa
          #          print(f"Signal: Aidat ödendi - {instance.daire} {instance.ay}/{instance.yil}")
           #         instance.odeme_yap(instance.odeme_tarihi, instance.kim_odedi, instance.odeme_notu)
            #    else:
                    # Ödeme iptal edildiyse
             #       print(f"Signal: Aidat ödemesi iptal edildi - {instance.daire} {instance.ay}/{instance.yil}")
              #      instance.odeme_iptal()
        #except Aidat.DoesNotExist:
         #   pass