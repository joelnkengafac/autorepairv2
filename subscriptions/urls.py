from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # ── Garagiste ──────────────────────────────────────────────────────────
    path('',                             views.subscription_dashboard, name='dashboard'),
    path('choisir-formule/',             views.choose_plan,            name='choose_plan'),
    path('payer/<int:plan_id>/',         views.initiate_payment,       name='initiate_payment'),
    path('paiement/<int:payment_id>/',   views.payment_pending,        name='payment_pending'),
    path('historique/',                  views.payment_history,        name='payment_history'),

    # ── Admin ───────────────────────────────────────────────────────────────
    path('admin/paiements/',                     views.admin_payments_list,    name='admin_payments_list'),
    path('admin/paiements/<int:payment_id>/',    views.admin_payment_detail,   name='admin_payment_detail'),
    path('admin/abonnements/',                   views.admin_subscriptions_list, name='admin_subscriptions_list'),
]
