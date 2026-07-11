# /var/www/html/auto/autorepair_project/reviews/templatetags/review_extras.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplie deux valeurs : {{ value|multiply:arg }}"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def divide(value, arg):
    """Divise deux valeurs : {{ value|divide:arg }}"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0