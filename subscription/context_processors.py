"""
Context processor : injecte dans tous les templates les données
utiles à la navbar et aux alertes (abonnement, paiements en attente, etc.)
"""
from django.utils import timezone


def subscription_context(request):
    ctx = {
        'sub_pending_count': 0,       # paiements en attente (admin)
        'user_subscription': None,     # abonnement actif du garagiste
        'sub_expiring_soon': False,    # abonnement qui expire dans <= 7j
        'garage_is_active': False,     # garage visible ou non
    }

    if not request.user.is_authenticated:
        return ctx

    # ── Garagiste : abonnement actif ─────────────────────────────────────────
    if getattr(request.user, 'role', None) == 'garage':
        try:
            from garages.models import Garage
            from subscription.models import Subscription
            garage = Garage.objects.get(user=request.user)
            ctx['garage_is_active'] = garage.is_active
            active_sub = Subscription.objects.filter(
                garage=garage,
                status=Subscription.STATUS_ACTIVE,
                end_date__gt=timezone.now()
            ).select_related('plan').first()
            if active_sub:
                ctx['user_subscription']  = active_sub
                ctx['sub_expiring_soon']  = active_sub.days_remaining <= 7
        except Exception:
            pass

    # ── Admin : paiements en attente ─────────────────────────────────────────
    if request.user.is_staff or request.user.is_superuser:
        try:
            from subscription.models import Payment
            ctx['sub_pending_count'] = Payment.objects.filter(
                status=Payment.STATUS_PENDING
            ).count()
        except Exception:
            pass

    return ctx
