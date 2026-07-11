from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Plan, Subscription, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display  = ('name', 'period', 'price', 'duration_days', 'is_active')
    list_editable = ('is_active',)
    ordering      = ('price',)


class PaymentInline(admin.TabularInline):
    model       = Payment
    extra       = 0
    readonly_fields = ('reference', 'created_at', 'confirmed_at', 'confirmed_by')
    fields      = ('method', 'phone_number', 'amount', 'status',
                   'operator_ref', 'reference', 'confirmed_by', 'confirmed_at')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display  = ('garage', 'plan', 'status_badge', 'start_date',
                     'end_date', 'days_remaining', 'created_at')
    list_filter   = ('status', 'plan')
    search_fields = ('garage__name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines       = [PaymentInline]

    def status_badge(self, obj):
        colors = {
            'en_attente': '#f0ad4e',
            'actif':      '#5cb85c',
            'expire':     '#d9534f',
            'annule':     '#777',
        }
        color = colors.get(obj.status, '#777')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;'
            'border-radius:4px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'

    def days_remaining(self, obj):
        return f"{obj.days_remaining} j"
    days_remaining.short_description = 'Jours restants'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ('reference', 'garage_name', 'plan_name', 'amount',
                     'method', 'phone_number', 'status_badge', 'created_at', 'action_btn')
    list_filter   = ('status', 'method')
    search_fields = ('reference', 'phone_number', 'subscription__garage__name')
    readonly_fields = ('reference', 'created_at', 'confirmed_at', 'confirmed_by')
    actions       = ['validate_payments', 'reject_payments']

    def garage_name(self, obj):
        return obj.subscription.garage.name
    garage_name.short_description = 'Garage'

    def plan_name(self, obj):
        return obj.subscription.plan.name
    plan_name.short_description = 'Formule'

    def status_badge(self, obj):
        colors = {
            'en_attente': '#f0ad4e',
            'valide':     '#5cb85c',
            'echoue':     '#d9534f',
            'rembourse':  '#5bc0de',
        }
        color = colors.get(obj.status, '#777')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;'
            'border-radius:4px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'

    def action_btn(self, obj):
        if obj.status == 'en_attente':
            return format_html(
                '<a href="/abonnement/admin/paiements/{}/confirmer/" '
                'style="background:#1F3864;color:#fff;padding:4px 10px;'
                'border-radius:4px;font-size:12px;text-decoration:none;">'
                'Traiter</a>', obj.pk
            )
        return '—'
    action_btn.short_description = 'Action'

    @admin.action(description='Valider les paiements sélectionnés')
    def validate_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(status=Payment.STATUS_PENDING):
            payment.status       = Payment.STATUS_COMPLETED
            payment.confirmed_by = request.user
            payment.confirmed_at = timezone.now()
            payment.save()
            payment.subscription.activate()
            count += 1
        self.message_user(request, f"{count} paiement(s) validé(s).")

    @admin.action(description='Rejeter les paiements sélectionnés')
    def reject_payments(self, request, queryset):
        count = 0
        for payment in queryset.filter(status=Payment.STATUS_PENDING):
            payment.status = Payment.STATUS_FAILED
            payment.save()
            payment.subscription.status = Subscription.STATUS_CANCELED
            payment.subscription.save()
            count += 1
        self.message_user(request, f"{count} paiement(s) rejeté(s).")
