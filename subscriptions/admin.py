from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Plan, Subscription, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display  = ('name', 'duration', 'price_display', 'is_active', 'created_at')
    list_filter   = ('is_active', 'duration')
    search_fields = ('name',)

    def price_display(self, obj):
        return f"{obj.price:,} XAF".replace(',', ' ')
    price_display.short_description = "Prix"


class PaymentInline(admin.TabularInline):
    model  = Payment
    extra  = 0
    fields = ('plan', 'amount', 'provider', 'phone_number', 'status',
              'reference', 'initiated_at', 'confirmed_at')
    readonly_fields = ('initiated_at', 'confirmed_at')
    can_delete = False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display   = ('garage', 'plan', 'status_badge', 'start_date',
                      'end_date', 'days_left', 'auto_renew')
    list_filter    = ('status', 'plan', 'auto_renew')
    search_fields  = ('garage__name',)
    readonly_fields= ('created_at', 'updated_at')
    inlines        = [PaymentInline]
    actions        = ['expire_selected']

    def status_badge(self, obj):
        colors = {
            'actif':       'green',
            'expire':      'red',
            'en_attente':  'orange',
            'annule':      'grey',
        }
        color = colors.get(obj.status, 'grey')
        return format_html(
            '<span style="color:white;background:{};padding:3px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"

    def days_left(self, obj):
        d = obj.days_remaining()
        if obj.status != 'actif':
            return '—'
        color = 'red' if d <= 7 else ('orange' if d <= 15 else 'green')
        return format_html('<b style="color:{};">{} j</b>', color, d)
    days_left.short_description = "Jours restants"

    def expire_selected(self, request, queryset):
        for sub in queryset:
            sub.expire()
        self.message_user(request, f"{queryset.count()} abonnement(s) expiré(s).")
    expire_selected.short_description = "Expirer les abonnements sélectionnés"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display   = ('id', 'garage_name', 'plan', 'amount_display',
                      'provider_badge', 'phone_number', 'status_badge',
                      'initiated_at', 'confirmed_at')
    list_filter    = ('status', 'provider', 'plan')
    search_fields  = ('subscription__garage__name', 'phone_number', 'reference')
    readonly_fields= ('initiated_at', 'confirmed_at', 'subscription')
    actions        = ['confirm_payments', 'reject_payments']

    def garage_name(self, obj):
        return obj.subscription.garage.name
    garage_name.short_description = "Garage"

    def amount_display(self, obj):
        return f"{obj.amount:,} XAF".replace(',', ' ')
    amount_display.short_description = "Montant"

    def provider_badge(self, obj):
        colors = {
            'orange_money':     '#FF6600',
            'mtn_momo':         '#FFCC00',
            'virement_manuel':  '#336699',
        }
        color = colors.get(obj.provider, '#888')
        return format_html(
            '<span style="color:white;background:{};padding:3px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color, obj.get_provider_display()
        )
    provider_badge.short_description = "Opérateur"

    def status_badge(self, obj):
        colors = {
            'en_attente': 'orange',
            'succes':     'green',
            'echec':      'red',
            'rembourse':  'purple',
        }
        color = colors.get(obj.status, 'grey')
        return format_html(
            '<span style="color:white;background:{};padding:3px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"

    def confirm_payments(self, request, queryset):
        confirmed = 0
        for p in queryset.filter(status=Payment.STATUS_PENDING):
            p.confirm()
            confirmed += 1
        self.message_user(request, f"{confirmed} paiement(s) confirmé(s).")
    confirm_payments.short_description = "Confirmer les paiements sélectionnés"

    def reject_payments(self, request, queryset):
        queryset.filter(status=Payment.STATUS_PENDING).update(
            status=Payment.STATUS_FAILED
        )
        self.message_user(request, "Paiements rejetés.")
    reject_payments.short_description = "Rejeter les paiements sélectionnés"
