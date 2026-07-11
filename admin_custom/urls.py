from django.urls import path
from . import views

app_name = 'admin_custom'

urlpatterns = [
    path('',                        views.dashboard,    name='dashboard'),
    path('utilisateurs/',           views.user_list,    name='users'),
    path('utilisateurs/<int:pk>/',  views.user_detail,  name='user_detail'),
    path('garages/',                views.garage_list,  name='garages'),
    path('garages/<int:pk>/',       views.garage_detail, name='garage_detail'),
    path('avis/',                   views.review_list,  name='reviews'),
    path('statistiques/',           views.stats,        name='stats'),
]
