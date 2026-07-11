from django.contrib import admin
from .models import ServiceCategory, GarageService

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(GarageService)
class GarageServiceAdmin(admin.ModelAdmin):
    list_display = ('garage', 'service', 'price_starting_at')
    list_filter = ('service',)