from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Formulaire de création
    path('garage/<int:garage_pk>/add/', views.create_review, name='create'),
    
    # Modification/Suppression
    path('<int:review_pk>/edit/', views.edit_review, name='edit'),
    path('<int:review_pk>/delete/', views.delete_review, name='delete'),
    
    # API JSON (optionnel)
    path('garage/<int:garage_pk>/rating/', views.garage_rating_api, name='rating_api'),
]