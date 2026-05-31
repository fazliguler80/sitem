from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def para( value ):
    """Sayıyı Türk Lirası formatında göster (1.000,00 TL)"""
    try:
        if value is None:
            return "0,00"
        # Decimal'e çevir
        if isinstance(value, str):
            value = Decimal(value.replace(',', '.'))
        elif isinstance(value, float):
            value = Decimal(str(value))
        
        # Formatla: binlik ayraç nokta, ondalık virgül
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except:
        return str(value)

@register.filter
def yuzde( value ):
    """Yüzde formatı (65.50%)"""
    try:
        if value is None:
            return "0,00%"
        if isinstance(value, str):
            value = Decimal(value.replace(',', '.'))
        elif isinstance(value, float):
            value = Decimal(str(value))
        formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted}%"
    except:
        return f"{value}%"