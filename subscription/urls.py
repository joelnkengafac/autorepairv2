from django.urls import path
from . import views

app_name = 'subscription'

urlpatterns = [
    # Garagiste
    path('',                          views.choose_plan,         name='choose_plan'),
    path('payer/<int:plan_id>/',      views.initiate_payment,    name='initiate_payment'),
    path('attente/<int:pk>/',         views.payment_pending,     name='payment_pending'),
    path('mon-abonnement/',           views.subscription_dashboard, name='dashboard'),

    # Admin
    path('admin/paiements/',          views.admin_payments,      name='admin_payments'),
    path('admin/paiements/<int:pk>/confirmer/', views.admin_confirm_payment, name='admin_confirm_payment'),
    path('admin/abonnements/',        views.admin_subscriptions, name='admin_subscriptions'),
]
