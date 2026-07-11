import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Garage
from .forms import GarageCreateForm, GarageEditForm
from .utils import calculate_distance, geocode_address, geocode_city

# Coordonnées par défaut : centre de Yaoundé
DEFAULT_LAT = 3.8607
DEFAULT_LON = 11.5205


def garage_list(request):
    """
    Liste les garages ouverts, triés par distance par rapport à la position
    de l'utilisateur.

    La position est déterminée dans cet ordre de priorité :
      1. Paramètres ?lat=&lon= dans l'URL (depuis la géoloc JS du navigateur)
      2. Paramètre ?city= → géocodé par Nominatim
      3. Position par défaut : Yaoundé
    """
    garages = Garage.objects.filter(is_open=True, is_active=True).order_by('name')

    # ── 1. Position depuis l'URL (lat/lon directs) ───────────────────────────
    user_lat = request.GET.get('lat')
    user_lon = request.GET.get('lon')
    city_query = request.GET.get('city', '').strip()
    geocode_error = None

    # ── 2. Géocodage d'une ville via Nominatim ───────────────────────────────
    if city_query and not (user_lat and user_lon):
        result = geocode_city(city_query)
        if result:
            user_lat = result['lat']
            user_lon = result['lon']
        else:
            geocode_error = f"Ville « {city_query} » introuvable. Position par défaut utilisée."

    # ── 3. Fallback : Yaoundé ────────────────────────────────────────────────
    try:
        user_lat = float(user_lat) if user_lat else DEFAULT_LAT
        user_lon = float(user_lon) if user_lon else DEFAULT_LON
    except (ValueError, TypeError):
        user_lat, user_lon = DEFAULT_LAT, DEFAULT_LON

    # ── Calcul des distances ─────────────────────────────────────────────────
    garages_with_distance = []
    for g in garages:
        try:
            dist = calculate_distance(
                user_lat, user_lon,
                float(g.latitude), float(g.longitude)
            )
            garages_with_distance.append({'garage': g, 'distance': dist})
        except Exception as e:
            print(f"[AutoRepair] Erreur distance {g.name}: {e}")

    garages_sorted = sorted(garages_with_distance, key=lambda k: k['distance'])

    # ── Sérialisation JSON pour la carte Leaflet ─────────────────────────────
    garages_json = json.dumps([
        {
            'id': item['garage'].pk,
            'name': item['garage'].name,
            'city': item['garage'].city,
            'latitude': float(item['garage'].latitude),
            'longitude': float(item['garage'].longitude),
            'distance': item['distance'],
        }
        for item in garages_sorted
        if item['garage'].latitude and item['garage'].longitude
    ])

    return render(request, 'garages/garage_list.html', {
        'garages': garages_sorted,
        'garages_json': garages_json,
        'user_lat': user_lat,
        'user_lon': user_lon,
        'city_query': city_query,
        'geocode_error': geocode_error,
    })


@login_required
def garage_create(request):
    """
    Crée le profil d'un garage.
    La latitude/longitude peut être remplie automatiquement
    via l'API Nominatim depuis le formulaire (JavaScript).
    """
    if request.user.role != 'garage':
        messages.error(request, "Seuls les comptes professionnels peuvent créer un garage.")
        return redirect('core:home')

    if hasattr(request.user, 'garage_profile'):
        messages.info(request, "Vous avez déjà un profil garage.")
        return redirect('garages:garage_detail', pk=request.user.garage_profile.pk)

    if request.method == 'POST':
        form = GarageCreateForm(request.POST)
        if form.is_valid():
            # Si lat/lon non remplis, géocodage serveur via Nominatim
            garage = form.save(commit=False)
            if not garage.latitude or not garage.longitude:
                result = geocode_address(garage.address, garage.city)
                if result:
                    garage.latitude  = result['lat']
                    garage.longitude = result['lon']
                    messages.info(request,
                        f"Position géolocalisée automatiquement via OpenStreetMap : "
                        f"{result['lat']:.6f}, {result['lon']:.6f}")
                else:
                    messages.warning(request,
                        "Impossible de géolocaliser l'adresse. "
                        "Veuillez renseigner la latitude et la longitude manuellement.")
            garage.user = request.user
            garage.save()
            messages.success(request, f"Garage « {garage.name} » créé avec succès !")
            return redirect('garages:garage_detail', pk=garage.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = GarageCreateForm(initial={
            'latitude': '',
            'longitude': '',
            'is_open': True,
        })

    return render(request, 'garages/garage_form.html', {'form': form})


def garage_detail(request, pk):
    """Détail d'un garage avec mini-carte et distance."""
    garage = get_object_or_404(Garage, pk=pk)

    try:
        user_lat = float(request.GET.get('lat', DEFAULT_LAT))
        user_lon = float(request.GET.get('lon', DEFAULT_LON))
        distance = calculate_distance(
            user_lat, user_lon,
            float(garage.latitude), float(garage.longitude)
        )
    except Exception:
        distance = None
        user_lat, user_lon = DEFAULT_LAT, DEFAULT_LON

    # Avis
    from reviews.models import Review
    reviews = Review.objects.filter(garage=garage).select_related('user').order_by('-created_at')
    avg = (sum(r.rating for r in reviews) / len(reviews)) if reviews else 0
    user_has_reviewed = False
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        user_has_reviewed = user_review is not None

    return render(request, 'garages/garage_detail.html', {
        'garage': garage,
        'distance': distance,
        'user_lat': user_lat,
        'user_lon': user_lon,
        'reviews': reviews,
        'average_rating': round(avg, 1),
        'total_reviews': len(reviews),
        'user_has_reviewed': user_has_reviewed,
        'user_review': user_review,
    })


@login_required
def garage_edit(request, pk):
    """
    Permet au garagiste propriétaire de modifier son profil.
    - Seul le propriétaire du garage peut y accéder.
    - La latitude/longitude est mise à jour via Nominatim si l'adresse change.
    """
    garage = get_object_or_404(Garage, pk=pk)

    # Sécurité : seul le propriétaire du garage peut modifier
    if garage.user != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à modifier ce garage.")
        return redirect('garages:garage_detail', pk=pk)

    if request.method == 'POST':
        form = GarageEditForm(request.POST, request.FILES, instance=garage)
        if form.is_valid():
            updated = form.save(commit=False)

            # Si l'adresse ou la ville a changé et que lat/lon sont vides → regéocoder
            addr_changed = (
                form.cleaned_data.get('address') != garage.address or
                form.cleaned_data.get('city') != garage.city
            )
            lat_empty = not form.cleaned_data.get('latitude')
            lon_empty = not form.cleaned_data.get('longitude')

            if (addr_changed or lat_empty or lon_empty):
                result = geocode_address(updated.address, updated.city)
                if result:
                    updated.latitude  = result['lat']
                    updated.longitude = result['lon']
                    messages.info(
                        request,
                        f"Position mise à jour via OpenStreetMap : "
                        f"{result['lat']:.6f}, {result['lon']:.6f}"
                    )

            updated.save()
            messages.success(request, f"Garage « {updated.name} » mis à jour avec succès !")
            return redirect('garages:garage_detail', pk=pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = GarageEditForm(instance=garage)

    return render(request, 'garages/garage_edit.html', {
        'form': form,
        'garage': garage,
    })
