from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden

from garages.models import Garage
from .models import Plan, Subscription, Payment
from .forms import PaymentInitForm, PaymentConfirmForm


def is_admin(user):
    return user.is_staff or user.is_superuser


# ─── GARAGISTE ───────────────────────────────────────────────────────────────

@login_required
def choose_plan(request):
    """
    Le garagiste choisit sa formule d'abonnement.
    Accessible uniquement si le garage n'a pas d'abonnement actif.
    """
    if request.user.role != 'garage':
        return HttpResponseForbidden("Réservé aux garagistes.")

    garage = get_object_or_404(Garage, user=request.user)

    # Vérifier s'il y a un abonnement actif
    active_sub = Subscription.objects.filter(
        garage=garage, status=Subscription.STATUS_ACTIVE
    ).first()

    plans = Plan.objects.filter(is_active=True)

    return render(request, 'subscription/choose_plan.html', {
        'garage':     garage,
        'plans':      plans,
        'active_sub': active_sub,
    })


@login_required
def initiate_payment(request, plan_id):
    """
    Le garagiste initie le paiement pour une formule choisie.
    Crée un Subscription en attente et un Payment en attente.
    """
    if request.user.role != 'garage':
        return HttpResponseForbidden()

    garage = get_object_or_404(Garage, user=request.user)
    plan   = get_object_or_404(Plan, pk=plan_id, is_active=True)

    # Empêcher un double abonnement actif
    if Subscription.objects.filter(garage=garage, status=Subscription.STATUS_ACTIVE).exists():
        messages.warning(request, "Vous avez déjà un abonnement actif.")
        return redirect('subscription:dashboard')

    if request.method == 'POST':
        form = PaymentInitForm(request.POST)
        if form.is_valid():
            # Créer l'abonnement en attente
            sub = Subscription.objects.create(
                garage=garage,
                plan=plan,
                status=Subscription.STATUS_PENDING,
            )
            # Créer le paiement en attente
            payment = Payment.objects.create(
                subscription=sub,
                amount=plan.price,
                method=form.cleaned_data['method'],
                phone_number=form.cleaned_data['phone_number'],
                status=Payment.STATUS_PENDING,
            )
            messages.success(
                request,
                f"Demande de paiement enregistrée (réf. {payment.reference}). "
                f"Effectuez le paiement de {plan.price} FCFA au numéro indiqué, "
                f"puis attendez la validation de l'administrateur."
            )
            return redirect('subscription:payment_pending', pk=payment.pk)
    else:
        # Pré-remplir avec le numéro du compte garagiste
        form = PaymentInitForm(initial={
            'phone_number': request.user.phone_number
        })

    return render(request, 'subscription/initiate_payment.html', {
        'form':   form,
        'plan':   plan,
        'garage': garage,
    })


@login_required
def payment_pending(request, pk):
    """Page d'attente affichée après soumission du paiement."""
    payment = get_object_or_404(
        Payment, pk=pk, subscription__garage__user=request.user
    )
    return render(request, 'subscription/payment_pending.html', {
        'payment': payment,
    })


@login_required
def subscription_dashboard(request):
    """Tableau de bord abonnement du garagiste."""
    if request.user.role != 'garage':
        return HttpResponseForbidden()

    garage = get_object_or_404(Garage, user=request.user)
    subscriptions = Subscription.objects.filter(
        garage=garage
    ).select_related('plan').prefetch_related('payments').order_by('-created_at')

    active_sub = subscriptions.filter(status=Subscription.STATUS_ACTIVE).first()

    return render(request, 'subscription/dashboard.html', {
        'garage':        garage,
        'subscriptions': subscriptions,
        'active_sub':    active_sub,
    })


# ─── ADMIN ───────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_payments(request):
    """Vue admin : liste tous les paiements en attente et l'historique."""
    pending  = Payment.objects.filter(
        status=Payment.STATUS_PENDING
    ).select_related('subscription__garage', 'subscription__plan').order_by('-created_at')

    history  = Payment.objects.exclude(
        status=Payment.STATUS_PENDING
    ).select_related('subscription__garage', 'subscription__plan').order_by('-created_at')[:50]

    return render(request, 'subscription/admin_payments.html', {
        'pending': pending,
        'history': history,
    })


@login_required
@user_passes_test(is_admin)
def admin_confirm_payment(request, pk):
    """
    L'admin valide ou rejette un paiement.
    Si validé → active l'abonnement → rend le garage visible.
    """
    payment = get_object_or_404(Payment, pk=pk)

    if request.method == 'POST':
        form = PaymentConfirmForm(request.POST, instance=payment)
        if form.is_valid():
            action = request.POST.get('action')
            payment = form.save(commit=False)
            payment.confirmed_by = request.user
            payment.confirmed_at = timezone.now()

            if action == 'validate':
                payment.status = Payment.STATUS_COMPLETED
                payment.save()
                # Activer l'abonnement et rendre le garage visible
                payment.subscription.activate()
                messages.success(
                    request,
                    f"Paiement {payment.reference} validé. "
                    f"Le garage « {payment.subscription.garage.name} » est maintenant visible."
                )
            elif action == 'reject':
                payment.status = Payment.STATUS_FAILED
                payment.subscription.status = Subscription.STATUS_CANCELED
                payment.subscription.save()
                payment.save()
                messages.warning(
                    request,
                    f"Paiement {payment.reference} rejeté."
                )

            return redirect('subscription:admin_payments')
    else:
        form = PaymentConfirmForm(instance=payment)

    return render(request, 'subscription/admin_confirm.html', {
        'payment': payment,
        'form':    form,
    })


@login_required
@user_passes_test(is_admin)
def admin_subscriptions(request):
    """Vue admin : liste tous les abonnements."""
    subscriptions = Subscription.objects.select_related(
        'garage', 'plan'
    ).prefetch_related('payments').order_by('-created_at')

    return render(request, 'subscription/admin_subscriptions.html', {
        'subscriptions': subscriptions,
    })
