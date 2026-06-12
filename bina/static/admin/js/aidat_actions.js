// bina/static/admin/js/aidat_actions.js

document.addEventListener('DOMContentLoaded', function() {
    // Ödeme butonları
    document.querySelectorAll('.odeme-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const aidatId = this.dataset.id;
            const odemeTarihi = prompt("Ödeme tarihini giriniz (YYYY-MM-DD):", new Date().toISOString().slice(0,10));
            if (odemeTarihi) {
                const odemeNotu = prompt("Ödeme notu (isteğe bağlı):", "");
                fetch(`/admin/bina/aidat/ajax/odeme-yap/${aidatId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        'odeme_tarihi': odemeTarihi,
                        'odeme_notu': odemeNotu
                    })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    if (data.success) location.reload();
                })
                .catch(error => console.error('Hata:', error));
            }
        });
    });

    // İptal butonları
    document.querySelectorAll('.iptal-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const aidatId = this.dataset.id;
            if (confirm('Ödemeyi iptal etmek depozito hareketini de silecektir. Devam etmek istiyor musunuz?')) {
                fetch(`/admin/bina/aidat/ajax/odeme-iptal/${aidatId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    if (data.success) location.reload();
                })
                .catch(error => console.error('Hata:', error));
            }
        });
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}