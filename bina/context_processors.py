from bina.models import Site

def site_selector(request):
    """Admin paneli için site seçici context processor"""
    sites = []
    aktif_site_id = None
    
    # Sadece admin sayfalarında göster
    if request.path.startswith('/admin/'):
        sites = Site.objects.filter(aktif=True)
        aktif_site_id = request.session.get('aktif_site_id')
    
    return {
        'sites': sites,
        'aktif_site_id': aktif_site_id,
    }