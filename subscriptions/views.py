from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from garages.models import Garage
from .models import Plan, Subscription, Payment
from .forms import SubscriptionChoiceForm, PaymentInitForm, PaymentConfirmForm, PaymentRejectForm


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def is_admin(user):
    return user.is_staff or user.is_superuser

def get_garage_or_redirect(user):
    """Récupère le garage du garagiste connecté."""
    try:
        return user.garage_profile
    except Garage.DoesNotExist:
        return None


# ─── GARAGISTE : TABLEAU DE BORD ABONNEMENT ──────────────────────────────────

@login_required
def subscription_dashboard(request):
    """
    Tableau de bord abonnement du garagiste.
    Affiche le statut actuel et le bouton de souscription / renouvellement.
    """
    if request.user.role != 'garage':
        messages.error(request, "Accès réservé aux garagistes.")
        return redirect('core:home')

    garage = get_garage_or_redirect(request.user)
    if not garage:
        messages.warning(request, "Créez d'abord votre profil garage.")
        return redirect('garages:garage_create')

    subscription = getattr(garage, 'subscription', None)
    pending_payment = None
    if subscription:
        pending_payment = subscription.payments.filter(
            status=Payment.STATUS_PENDING
        ).first()

    return render(request, 'subscriptions/dashboard.html', {
        'garage':          garage,
        'subscription':    subscription,
        'pending_payment': pending_payment,
        'plans':           Plan.objects.filter(is_active=True).order_by('price'),
    })


@login_required
def choose_plan(request):
    """Étape 1 : le garagiste choisit sa formule."""
    if request.user.role != 'garage':
        return redirect('core:home')

    garage = get_garage_or_redirect(request.user)
    if not garage:
        return redirect('garages:garage_create')

    plans = Plan.objects.filter(is_active=True).order_by('price')

    if request.method == 'POST':
        form = SubscriptionChoiceForm(request.POST)
        if form.is_valid():
            plan = form.cleaned_data['plan']
            return redirect('subscriptions:initiate_payment', plan_id=plan.pk)
    else:
        form = SubscriptionChoiceForm()

    return render(request, 'subscriptions/choose_plan.html', {
        'form': form, 'plans': plans, 'garage': garage,
    })


@login_required
@transaction.atomic
def initiate_payment(request, plan_id):
    """
    Étape 2 : le garagiste saisit son numéro Mobile Money.
    Crée le paiement en attente + l'abonnement si inexistant.
    """
    if request.user.role != 'garage':
        return redirect('core:home')

    garage = get_garage_or_redirect(request.user)
    plan   = get_object_or_404(Plan, pk=plan_id, is_active=True)

    # Bloquer si un paiement est déjà en attente
    sub = getattr(garage, 'subscription', None)
    if sub and sub.payments.filter(status=Payment.STATUS_PENDING).exists():
        messages.warning(
            request,
            "Vous avez déjà un paiement en attente. "
            "Attendez sa validation ou contactez l'administrateur."
        )
        return redirect('subscriptions:dashboard')

    if request.method == 'POST':
        form = PaymentInitForm(request.POST)
        if form.is_valid():
            # Créer ou récupérer l'abonnement
            if not sub:
                sub = Subscription.objects.create(
                    garage=garage,
                    plan=plan,
                    status=Subscription.STATUS_PENDING,
                )
            else:
                sub.plan = plan
                sub.status = Subscription.STATUS_PENDING
                sub.save(update_fields=['plan', 'status'])

            # Créer le paiement
            payment = Payment.objects.create(
                subscription=sub,
                plan=plan,
                amount=plan.price,
                provider=form.cleaned_data['provider'],
                phone_number=form.cleaned_data['phone_number'],
                status=Payment.STATUS_PENDING,
            )

            messages.success(
                request,
                f"Votre demande de paiement de {plan.price} XAF via "
                f"{payment.get_provider_display()} a été enregistrée. "
                f"Un administrateur va valider votre paiement sous 24h."
            )
            return redirect('subscriptions:payment_pending', payment_id=payment.pk)
    else:
        form = PaymentInitForm()

    return render(request, 'subscriptions/initiate_payment.html', {
        'form': form, 'plan': plan, 'garage': garage,
    })


@login_required
def payment_pending(request, payment_id):
    """Page d'attente après soumission du paiement."""
    garage  = get_garage_or_redirect(request.user)
    payment = get_object_or_404(
        Payment, pk=payment_id, subscription__garage=garage
    )
    return render(request, 'subscriptions/payment_pending.html', {
        'payment': payment,
        'garage':  garage,
    })


@login_required
def payment_history(request):
    """Historique des paiements du garagiste."""
    garage = get_garage_or_redirect(request.user)
    if not garage:
        return redirect('garages:garage_create')

    sub      = getattr(garage, 'subscription', None)
    payments = sub.payments.order_by('-initiated_at') if sub else []

    return render(request, 'subscriptions/payment_history.html', {
        'garage':   garage,
        'payments': payments,
        'sub':      sub,
    })


# ─── ADMIN : GESTION DES PAIEMENTS ───────────────────────────────────────────

@user_passes_test(is_admin)
def admin_payments_list(request):
    """Liste tous les paiements — vue admin."""
    status_filter = request.GET.get('status', '')
    qs = Payment.objects.select_related(
        'subscription__garage', 'plan'
    ).order_by('-initiated_at')

    if status_filter:
        qs = qs.filter(status=status_filter)

    # Statistiques rapides
    stats = {
        'total':     Payment.objects.count(),
        'pending':   Payment.objects.filter(status=Payment.STATUS_PENDING).count(),
        'success':   Payment.objects.filter(status=Payment.STATUS_SUCCESS).count(),
        'failed':    Payment.objects.filter(status=Payment.STATUS_FAILED).count(),
        'revenue':   sum(
            p.amount for p in Payment.objects.filter(status=Payment.STATUS_SUCCESS)
        ),
    }

    return render(request, 'subscriptions/admin/payments_list.html', {
        'payments':      qs,
        'stats':         stats,
        'status_filter': status_filter,
        'status_choices': Payment.STATUS_CHOICES,
    })


@user_passes_test(is_admin)
def admin_payment_detail(request, payment_id):
    """Détail d'un paiement — confirmer ou rejeter."""
    payment = get_object_or_404(
        Payment.objects.select_related('subscription__garage', 'plan'),
        pk=payment_id
    )
    confirm_form = PaymentConfirmForm()
    reject_form  = PaymentRejectForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'confirm':
            confirm_form = PaymentConfirmForm(request.POST)
            if confirm_form.is_valid():
                payment.confirm(
                    reference=confirm_form.cleaned_data['reference'],
                    admin_notes=confirm_form.cleaned_data.get('admin_notes', ''),
                )
                messages.success(
                    request,
                    f"Paiement #{payment.pk} confirmé. "
                    f"Le garage «{payment.subscription.garage.name}» est maintenant actif."
                )
                return redirect('subscriptions:admin_payments_list')

        elif action == 'reject':
            reject_form = PaymentRejectForm(request.POST)
            if reject_form.is_valid():
                payment.reject(reason=reject_form.cleaned_data['reason'])
                messages.warning(request, f"Paiement #{payment.pk} rejeté.")
                return redirect('subscriptions:admin_payments_list')

    return render(request, 'subscriptions/admin/payment_detail.html', {
        'payment':      payment,
        'confirm_form': confirm_form,
        'reject_form':  reject_form,
    })


@user_passes_test(is_admin)
def admin_subscriptions_list(request):
    """Liste tous les abonnements avec leur statut."""
    subs = Subscription.objects.select_related(
        'garage', 'plan'
    ).order_by('-created_at')

    return render(request, 'subscriptions/admin/subscriptions_list.html', {
        'subscriptions': subs,
    })
