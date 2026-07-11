"""
Vues du tableau de bord administrateur personnalisé AutoRepair.
Accessible uniquement aux staff/superusers.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta

from accounts.models import User
from garages.models import Garage
from reviews.models import Review
from subscription.models import Plan, Subscription, Payment


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# ── TABLEAU DE BORD PRINCIPAL ─────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """
    Tableau de bord administrateur : KPIs, graphiques,
    dernières activités et alertes.
    """
    now = timezone.now()
    last_30 = now - timedelta(days=30)
    last_7  = now - timedelta(days=7)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_users    = User.objects.count()
    total_clients  = User.objects.filter(role='client').count()
    total_garages  = User.objects.filter(role='garage').count()
    total_garages_active = Garage.objects.filter(is_active=True).count()
    total_reviews  = Review.objects.count()

    # Abonnements
    sub_active   = Subscription.objects.filter(status='actif').count()
    sub_expiring = Subscription.objects.filter(
        status='actif',
        end_date__lte=now + timedelta(days=7),
        end_date__gt=now
    ).count()
    sub_expired_30 = Subscription.objects.filter(
        status='expire',
        updated_at__gte=last_30
    ).count()

    # Paiements
    pay_pending   = Payment.objects.filter(status='en_attente').count()
    pay_validated = Payment.objects.filter(
        status='valide', confirmed_at__gte=last_30
    ).count()
    revenue_30 = Payment.objects.filter(
        status='valide', confirmed_at__gte=last_30
    ).aggregate(total=Sum('amount'))['total'] or 0
    revenue_total = Payment.objects.filter(
        status='valide'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Nouveaux inscrits (7 derniers jours)
    new_users_7 = User.objects.filter(date_joined__gte=last_7).count()

    # ── DERNIÈRES ACTIVITÉS ────────────────────────────────────────────────────
    recent_payments = Payment.objects.filter(
        status='en_attente'
    ).select_related(
        'subscription__garage', 'subscription__plan'
    ).order_by('-created_at')[:5]

    recent_subs = Subscription.objects.select_related(
        'garage', 'plan'
    ).order_by('-created_at')[:5]

    recent_users = User.objects.order_by('-date_joined')[:5]

    # ── ABONNEMENTS EXPIRANT BIENTÔT ──────────────────────────────────────────
    expiring_soon = Subscription.objects.filter(
        status='actif',
        end_date__lte=now + timedelta(days=7),
        end_date__gt=now
    ).select_related('garage', 'plan').order_by('end_date')

    # ── RÉPARTITION PAR FORMULE ────────────────────────────────────────────────
    plans_stats = Plan.objects.annotate(
        count_active=Count(
            'subscriptions',
            filter=Q(subscriptions__status='actif')
        )
    ).values('name', 'count_active', 'price')

    return render(request, 'admin_custom/dashboard.html', {
        # KPIs utilisateurs
        'total_users':          total_users,
        'total_clients':        total_clients,
        'total_garages':        total_garages,
        'total_garages_active': total_garages_active,
        'total_reviews':        total_reviews,
        'new_users_7':          new_users_7,
        # KPIs abonnements
        'sub_active':           sub_active,
        'sub_expiring':         sub_expiring,
        'sub_expired_30':       sub_expired_30,
        # KPIs paiements
        'pay_pending':          pay_pending,
        'pay_validated':        pay_validated,
        'revenue_30':           revenue_30,
        'revenue_total':        revenue_total,
        # Listes
        'recent_payments':      recent_payments,
        'recent_subs':          recent_subs,
        'recent_users':         recent_users,
        'expiring_soon':        expiring_soon,
        'plans_stats':          plans_stats,
    })


# ── GESTION DES UTILISATEURS ─────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """Liste et filtrage de tous les utilisateurs."""
    role   = request.GET.get('role', '')
    search = request.GET.get('q', '').strip()

    users = User.objects.order_by('-date_joined')
    if role:
        users = users.filter(role=role)
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    return render(request, 'admin_custom/users.html', {
        'users':  users,
        'role':   role,
        'search': search,
    })


@login_required
@user_passes_test(is_admin)
def user_detail(request, pk):
    """Détail d'un utilisateur avec ses activités."""
    u = get_object_or_404(User, pk=pk)

    garage     = None
    subs       = []
    payments   = []

    if u.role == 'garage':
        try:
            garage   = Garage.objects.get(user=u)
            subs     = Subscription.objects.filter(
                garage=garage
            ).select_related('plan').order_by('-created_at')
            payments = Payment.objects.filter(
                subscription__garage=garage
            ).order_by('-created_at')
        except Garage.DoesNotExist:
            pass

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_active':
            u.is_active = not u.is_active
            u.save(update_fields=['is_active'])
            status = "activé" if u.is_active else "désactivé"
            messages.success(request, f"Compte {u.username} {status}.")
            return redirect('admin_custom:user_detail', pk=pk)
        if action == 'toggle_staff':
            u.is_staff = not u.is_staff
            u.save(update_fields=['is_staff'])
            messages.success(request, f"Droits staff mis à jour pour {u.username}.")
            return redirect('admin_custom:user_detail', pk=pk)

    return render(request, 'admin_custom/user_detail.html', {
        'u':        u,
        'garage':   garage,
        'subs':     subs,
        'payments': payments,
    })


# ── GESTION DES GARAGES ───────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def garage_list(request):
    """Liste des garages avec statut d'abonnement."""
    search = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    garages = Garage.objects.select_related('user').order_by('-created_at')
    if search:
        garages = garages.filter(
            Q(name__icontains=search) | Q(city__icontains=search)
        )
    if status == 'active':
        garages = garages.filter(is_active=True)
    elif status == 'inactive':
        garages = garages.filter(is_active=False)

    # Annoter avec le statut d'abonnement
    garage_data = []
    for g in garages:
        active_sub = Subscription.objects.filter(
            garage=g, status='actif'
        ).select_related('plan').first()
        garage_data.append({'garage': g, 'active_sub': active_sub})

    return render(request, 'admin_custom/garages.html', {
        'garage_data': garage_data,
        'search':      search,
        'status':      status,
    })


@login_required
@user_passes_test(is_admin)
def garage_detail(request, pk):
    """Détail d'un garage avec abonnements, avis et actions admin."""
    garage   = get_object_or_404(Garage, pk=pk)
    subs     = Subscription.objects.filter(
        garage=garage
    ).select_related('plan').prefetch_related('payments').order_by('-created_at')
    reviews  = Review.objects.filter(garage=garage).select_related('user').order_by('-created_at')
    active_sub = subs.filter(status='actif').first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_active':
            garage.is_active = not garage.is_active
            garage.save(update_fields=['is_active'])
            st = "visible" if garage.is_active else "invisible"
            messages.success(request, f"Garage « {garage.name} » maintenant {st}.")
            return redirect('admin_custom:garage_detail', pk=pk)

    return render(request, 'admin_custom/garage_detail.html', {
        'garage':     garage,
        'subs':       subs,
        'active_sub': active_sub,
        'reviews':    reviews,
    })


# ── GESTION DES AVIS ─────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def review_list(request):
    """Liste de tous les avis avec modération."""
    search = request.GET.get('q', '').strip()
    reviews = Review.objects.select_related(
        'garage', 'user'
    ).order_by('-created_at')
    if search:
        reviews = reviews.filter(
            Q(garage__name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(comment__icontains=search)
        )

    if request.method == 'POST':
        action    = request.POST.get('action')
        review_id = request.POST.get('review_id')
        review    = get_object_or_404(Review, pk=review_id)

        if action == 'verify':
            review.is_verified = True
            review.save(update_fields=['is_verified'])
            messages.success(request, "Avis vérifié.")
        elif action == 'delete':
            review.delete()
            messages.warning(request, "Avis supprimé.")

        return redirect('admin_custom:reviews')

    return render(request, 'admin_custom/reviews.html', {
        'reviews': reviews,
        'search':  search,
    })


# ── STATISTIQUES ──────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def stats(request):
    """Page de statistiques avancées."""
    now = timezone.now()

    # Revenus par formule
    revenue_by_plan = Payment.objects.filter(status='valide').values(
        'subscription__plan__name'
    ).annotate(total=Sum('amount'), count=Count('id')).order_by('-total')

    # Évolution mensuelle des paiements (6 derniers mois)
    monthly = []
    for i in range(5, -1, -1):
        start = (now - timedelta(days=30*i)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        end = (start + timedelta(days=32)).replace(day=1)
        total = Payment.objects.filter(
            status='valide',
            confirmed_at__gte=start,
            confirmed_at__lt=end
        ).aggregate(t=Sum('amount'))['t'] or 0
        monthly.append({
            'month': start.strftime('%b %Y'),
            'total': int(total),
        })

    # Répartition opérateurs
    orange_total = Payment.objects.filter(
        status='valide', method='orange_money'
    ).aggregate(t=Sum('amount'))['t'] or 0
    mtn_total = Payment.objects.filter(
        status='valide', method='mtn_momo'
    ).aggregate(t=Sum('amount'))['t'] or 0

    return render(request, 'admin_custom/stats.html', {
        'revenue_by_plan': revenue_by_plan,
        'monthly':         monthly,
        'orange_total':    orange_total,
        'mtn_total':       mtn_total,
    })
