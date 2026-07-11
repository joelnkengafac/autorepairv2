from django.urls import path
from . import views

app_name = 'repairs'

urlpatterns = [
    # Client
    path('mes-demandes/',                    views.client_requests,         name='client_requests'),
    path('nouvelle/<int:garage_id>/',        views.request_create,          name='request_create'),
    path('detail/<int:pk>/',                 views.request_detail_client,   name='request_detail_client'),
    path('annuler/<int:pk>/',                views.request_cancel_client,   name='request_cancel_client'),

    # Garage
    path('garage/demandes/',                 views.garage_requests,         name='garage_requests'),
    path('garage/demande/<int:pk>/',         views.request_detail_garage,   name='request_detail_garage'),
]
