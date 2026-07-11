from django.contrib import admin
from .models import Garage

@admin.register(Garage)
class GarageAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'is_open', 'user')
    list_filter = ('city', 'is_open')
    search_fields = ('name', 'city')