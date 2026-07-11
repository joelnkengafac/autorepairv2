from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/client/', views.dashboard_client_view, name='dashboard_client'),
    path('dashboard/garage/', views.dashboard_garage_view, name='dashboard_garage'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
]