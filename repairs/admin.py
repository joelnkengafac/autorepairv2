from django.contrib import admin
from .models import RepairRequest, Appointment


class AppointmentInline(admin.StackedInline):
    model = Appointment
    extra = 0


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'garage', 'type_service', 'status', 'created_at')
    list_filter = ('status', 'type_service')
    search_fields = ('owner__username', 'garage__name', 'vehicle_description')
    inlines = [AppointmentInline]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'repair_request', 'scheduled_at', 'status')
    list_filter = ('status',)
