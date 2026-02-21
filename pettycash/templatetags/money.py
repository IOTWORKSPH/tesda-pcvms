#money.py
from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def money(value):
    """
    Formats a number into Philippine Peso format with 2 decimal places.
    Safe for strings, None, and Decimal.
    """

    if value is None:
        return "0.00"

    try:
        # Convert to Decimal safely
        value = Decimal(value)
        return f"{value:,.2f}"
    except (InvalidOperation, ValueError, TypeError):
        return "0.00"