from django.urls import path
from . import views

app_name = 'garages'

urlpatterns = [
    path('',                    views.garage_list,   name='garage_list'),
    path('creer/',              views.garage_create, name='garage_create'),
    path('<int:pk>/',           views.garage_detail, name='garage_detail'),
    path('<int:pk>/modifier/',  views.garage_edit,   name='garage_edit'),   # ← nouveau
]
