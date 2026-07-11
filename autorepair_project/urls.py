from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Apps personnalisées
    path('compte/', include('accounts.urls')),
    path('garages/', include('garages.urls')),  # Sera créé plus tard
    path('services/', include('services.urls')),  # Sera créé plus tard
    path('reviews/', include('reviews.urls')),  # Sera créé plus tard
    path('', include('core.urls')),  # Page d'accueil
    path('avis/', include('reviews.urls')),  # ← Ajouter ici
    path('reparations/', include('repairs.urls')),
    path('messages/', include('messaging.urls')),
    path('abonnement/', include('subscription.urls')),
    path('dashboard-admin/', include('admin_custom.urls')),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)