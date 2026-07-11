from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q

from accounts.models import User
from garages.models import Garage
from repairs.models import RepairRequest
from reviews.models import Review
from messaging.models import Message
from subscription.models import Subscription, Payment, Plan


def is_admin(user):
    return user.is_active and (user.is_staff or user.is_superuser)


# ─── DASHBOARD PRINCIPAL ─────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """Tableau de bord admin avec statistiques globales."""
    now = timezone.now()

    # ── Statistiques utilisateurs
    total_users    = User.objects.count()
    total_clients  = User.objects.filter(role='client').count()
    total_garages  = User.objects.filter(role='garage').count()
    new_this_month = User.objects.filter(
        date_joined__month=now.month, date_joined__year=now.year
    ).count()

    # ── Statistiques garages
    total_garages_profiles = Garage.objects.count()
    active_garages         = Garage.objects.filter(is_active=True).count()
    inactive_garages       = Garage.objects.filter(is_active=False).count()

    # ── Statistiques abonnements
    active_subs   = Subscription.objects.filter(status='actif').count()
    pending_subs  = Subscription.objects.filter(status='en_attente').count()
    expired_subs  = Subscription.objects.filter(status='expire').count()
    expiring_soon = Subscription.objects.filter(
        status='actif', end_date__lte=now + timezone.timedelta(days=7)
    ).count()

    # ── Statistiques paiements
    pending_payments   = Payment.objects.filter(status='en_attente').count()
    total_revenue      = Payment.objects.filter(
        status='valide'
    ).aggregate(total=Sum('amount'))['total'] or 0
    revenue_this_month = Payment.objects.filter(
        status='valide',
        confirmed_at__month=now.month,
        confirmed_at__year=now.year
    ).aggregate(total=Sum('amount'))['total'] or 0

    # ── Statistiques réparations
    total_repairs   = RepairRequest.objects.count()
    pending_repairs = RepairRequest.objects.filter(status='en_attente').count()
    done_repairs    = RepairRequest.objects.filter(status='terminee').count()

    # ── Dernières activités
    recent_payments      = Payment.objects.select_related(
        'subscription__garage', 'subscription__plan'
    ).order_by('-created_at')[:5]

    recent_garages       = Garage.objects.select_related('user').order_by('-created_at')[:5]
    recent_users         = User.objects.order_by('-date_joined')[:5]

    # ── Garages expirant bientôt
    expiring_garages = Subscription.objects.filter(
        status='actif', end_date__lte=now + timezone.timedelta(days=7)
    ).select_related('garage', 'plan').order_by('end_date')

    return render(request, 'adminpanel/dashboard.html', {
        # Users
        'total_users':    total_users,
        'total_clients':  total_clients,
        'total_garages':  total_garages,
        'new_this_month': new_this_month,
        # Garages
        'total_garages_profiles': total_garages_profiles,
        'active_garages':         active_garages,
        'inactive_garages':       inactive_garages,
        # Abonnements
        'active_subs':    active_subs,
        'pending_subs':   pending_subs,
        'expired_subs':   expired_subs,
        'expiring_soon':  expiring_soon,
        # Paiements
        'pending_payments':   pending_payments,
        'total_revenue':      total_revenue,
        'revenue_this_month': revenue_this_month,
        # Réparations
        'total_repairs':   total_repairs,
        'pending_repairs': pending_repairs,
        'done_repairs':    done_repairs,
        # Listes
        'recent_payments':   recent_payments,
        'recent_garages':    recent_garages,
        'recent_users':      recent_users,
        'expiring_garages':  expiring_garages,
    })


# ─── GESTION DES GARAGES ─────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def garage_list(request):
    """Liste tous les garages avec filtres et recherche."""
    qs = Garage.objects.select_related('user').prefetch_related(
        'subscriptions', 'subscriptions__payments', 'subscriptions__plan'
    ).annotate(
        reviews_count=Count('reviews', distinct=True),
        repairs_count=Count('repair_requests', distinct=True),
    ).order_by('-created_at')

    # Filtres
    status_filter = request.GET.get('status', '')
    search        = request.GET.get('q', '').strip()
    city_filter   = request.GET.get('city', '').strip()

    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)

    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search) |
            Q(city__icontains=search)
        )
    if city_filter:
        qs = qs.filter(city__icontains=city_filter)

    cities = Garage.objects.values_list('city', flat=True).distinct().order_by('city')

    return render(request, 'adminpanel/garage_list.html', {
        'garages':       qs,
        'status_filter': status_filter,
        'search':        search,
        'city_filter':   city_filter,
        'cities':        cities,
        'total':         qs.count(),
    })


@login_required
@user_passes_test(is_admin)
def garage_detail(request, pk):
    """
    Vue détaillée d'un garage avec toutes ses informations et actions.
    """
    garage = get_object_or_404(
        Garage.objects.select_related('user').prefetch_related(
            'subscriptions__payments', 'subscriptions__plan',
            'repair_requests__owner', 'reviews__user',
        ),
        pk=pk
    )

    # Abonnement actif
    active_sub = garage.subscriptions.filter(status='actif').first()

    # Historique abonnements
    subscriptions = garage.subscriptions.select_related('plan').prefetch_related(
        'payments'
    ).order_by('-created_at')

    # Dernières demandes de réparation
    repairs = garage.repair_requests.select_related('owner').order_by('-created_at')[:10]

    # Avis
    reviews = garage.reviews.select_related('user').order_by('-created_at')[:10]
    avg_rating = reviews.aggregate(avg=Sum('rating'))
    total_reviews = garage.reviews.count()
    avg = (garage.reviews.aggregate(
        avg=Sum('rating')
    )['avg'] or 0) / total_reviews if total_reviews else 0

    # Statistiques
    stats = {
        'total_repairs':    garage.repair_requests.count(),
        'done_repairs':     garage.repair_requests.filter(status='terminee').count(),
        'pending_repairs':  garage.repair_requests.filter(status='en_attente').count(),
        'total_reviews':    total_reviews,
        'avg_rating':       round(avg, 1),
        'total_messages':   Message.objects.filter(
            Q(sender=garage.user) | Q(receiver=garage.user)
        ).count(),
    }

    return render(request, 'adminpanel/garage_detail.html', {
        'garage':        garage,
        'active_sub':    active_sub,
        'subscriptions': subscriptions,
        'repairs':       repairs,
        'reviews':       reviews,
        'stats':         stats,
    })


@login_required
@user_passes_test(is_admin)
def garage_toggle_active(request, pk):
    """Active ou désactive manuellement un garage."""
    garage = get_object_or_404(Garage, pk=pk)
    if request.method == 'POST':
        garage.is_active = not garage.is_active
        garage.save(update_fields=['is_active'])
        action = 'activé' if garage.is_active else 'désactivé'
        messages.success(request, f"Garage « {garage.name} » {action} avec succès.")
    return redirect('adminpanel:garage_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def garage_delete(request, pk):
    """Supprime un garage après confirmation."""
    garage = get_object_or_404(Garage, pk=pk)
    if request.method == 'POST':
        name = garage.name
        garage.user.delete()  # cascade supprime le garage
        messages.success(request, f"Garage « {name} » et son compte supprimés.")
        return redirect('adminpanel:garage_list')
    return render(request, 'adminpanel/garage_confirm_delete.html', {'garage': garage})


# ─── GESTION DES UTILISATEURS ────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """Liste tous les utilisateurs."""
    qs = User.objects.order_by('-date_joined')
    role_filter = request.GET.get('role', '')
    search      = request.GET.get('q', '').strip()

    if role_filter:
        qs = qs.filter(role=role_filter)
    if search:
        qs = qs.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    return render(request, 'adminpanel/user_list.html', {
        'users':       qs,
        'role_filter': role_filter,
        'search':      search,
        'total':       qs.count(),
    })


@login_required
@user_passes_test(is_admin)
def user_toggle_active(request, pk):
    """Active ou désactive un compte utilisateur."""
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        action = 'activé' if user.is_active else 'désactivé'
        messages.success(request, f"Compte « {user.username} » {action}.")
    return redirect('adminpanel:user_list')


# ─── GESTION DES RÉPARATIONS ─────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def repair_list(request):
    """Liste toutes les demandes de réparation."""
    qs = RepairRequest.objects.select_related('owner', 'garage').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    search        = request.GET.get('q', '').strip()

    if status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(
            Q(owner__username__icontains=search) |
            Q(garage__name__icontains=search) |
            Q(vehicle_description__icontains=search)
        )

    return render(request, 'adminpanel/repair_list.html', {
        'repairs':       qs,
        'status_filter': status_filter,
        'search':        search,
        'total':         qs.count(),
        'status_choices': RepairRequest.STATUS_CHOICES,
    })


# ─── STATISTIQUES ────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def statistics(request):
    """Page de statistiques détaillées."""
    now = timezone.now()

    # Revenus par mois (6 derniers mois)
    months_revenue = []
    for i in range(5, -1, -1):
        d = now - timezone.timedelta(days=30 * i)
        rev = Payment.objects.filter(
            status='valide',
            confirmed_at__month=d.month,
            confirmed_at__year=d.year
        ).aggregate(total=Sum('amount'))['total'] or 0
        months_revenue.append({
            'month': d.strftime('%b %Y'),
            'revenue': int(rev),
        })

    # Répartition par plan
    plan_stats = Plan.objects.annotate(
        sub_count=Count('subscriptions', filter=Q(subscriptions__status='actif'))
    ).values('name', 'sub_count')

    # Répartition par opérateur
    orange_count = Payment.objects.filter(status='valide', method='orange_money').count()
    mtn_count    = Payment.objects.filter(status='valide', method='mtn_momo').count()

    # Garages par ville
    city_stats = Garage.objects.filter(is_active=True).values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:8]

    return render(request, 'adminpanel/statistics.html', {
        'months_revenue': months_revenue,
        'plan_stats':     list(plan_stats),
        'orange_count':   orange_count,
        'mtn_count':      mtn_count,
        'city_stats':     city_stats,
    })
