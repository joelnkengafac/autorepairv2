import math
import urllib.request
import urllib.parse
import json


# ─── CALCUL DE DISTANCE (Haversine) ─────────────────────────────────────────

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en kilomètres entre deux points GPS
    via la formule de Haversine.
    """
    R = 6371.0  # Rayon de la Terre en km

    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)


# ─── GÉOCODAGE VIA NOMINATIM (OpenStreetMap) ────────────────────────────────

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
# User-Agent obligatoire selon les CGU Nominatim
NOMINATIM_HEADERS = {
    "User-Agent": "AutoRepair/1.0 (contact@autorepair.cm)",
    "Accept-Language": "fr",
}


def geocode_address(address, city, country="Cameroun"):
    """
    Convertit une adresse textuelle en coordonnées GPS (lat, lon)
    en interrogeant l'API Nominatim d'OpenStreetMap.

    Retourne un dict {"lat": float, "lon": float, "display_name": str}
    ou None si aucun résultat trouvé.
    """
    query = f"{address}, {city}, {country}"
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
    })
    url = f"{NOMINATIM_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers=NOMINATIM_HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", ""),
                }
    except Exception as e:
        print(f"[Nominatim] Erreur géocodage : {e}")

    return None


def geocode_city(city, country="Cameroun"):
    """
    Retourne les coordonnées GPS du centre d'une ville.
    Utilisé pour positionner la carte de recherche sur la ville de l'utilisateur.
    """
    return geocode_address("", city, country)


def reverse_geocode(lat, lon):
    """
    Convertit des coordonnées GPS en adresse lisible
    via l'API reverse de Nominatim.

    Retourne un dict {"address": str, "city": str} ou None.
    """
    params = urllib.parse.urlencode({
        "lat": lat,
        "lon": lon,
        "format": "json",
        "addressdetails": 1,
    })
    url = f"{NOMINATIM_REVERSE_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers=NOMINATIM_HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            addr = data.get("address", {})
            city = (addr.get("city")
                    or addr.get("town")
                    or addr.get("village")
                    or addr.get("county", ""))
            return {
                "address": data.get("display_name", ""),
                "city": city,
            }
    except Exception as e:
        print(f"[Nominatim] Erreur géocodage inverse : {e}")

    return None
