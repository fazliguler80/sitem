from bina.models import Site

def site_selector(request):
    """Site seçici context processor - Tüm sayfalar için"""
    sites = Site.objects.filter(aktif=True)
    aktif_site_id = None
    
    # Admin paneli için
    if request.path.startswith('/admin/'):
        aktif_site_id = request.session.get('aktif_site_id')
    
    # Portal için
    elif request.path.startswith('/portal/'):
        aktif_site_id = request.session.get('portal_site_id')
    
    # Ana sayfa ve diğer sayfalar için session'da kayıtlı site varsa
    else:
        # Önce admin sitesini kontrol et, yoksa portal sitesini kontrol et
        aktif_site_id = request.session.get('aktif_site_id') or request.session.get('portal_site_id')
    
    return {
        'sites': sites,
        'aktif_site_id': aktif_site_id,
    }