(function() {
    function updateLabel() {
        var maasTipi = document.getElementById('id_maas_tipi');
        var label = document.querySelector('.field-brut_maas label');
        var input = document.getElementById('id_brut_maas');
        
        if (maasTipi && label) {
            if (maasTipi.value === 'net') {
                label.innerHTML = 'Net Maaş (TL):';
                if (input) input.placeholder = '30000 TL (Net)';
            } else {
                label.innerHTML = 'Brüt Maaş (TL):';
                if (input) input.placeholder = '33030 TL (Brüt)';
            }
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateLabel);
    } else {
        updateLabel();
    }
    
    document.addEventListener('change', function(e) {
        if (e.target && e.target.id === 'id_maas_tipi') {
            updateLabel();
        }
    });
})();