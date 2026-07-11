from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm
from .models import User


def register_view(request):
    """Inscription simple"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Compte créé avec succès !')
            
            if user.role == User.ROLE_GARAGE:
                return redirect('accounts:dashboard_garage')
            return redirect('accounts:dashboard_client')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form, 'page_title': 'Inscription'})


def login_view(request):
    """Connexion simple"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user:
                login(request, user)
                messages.success(request, f'Bienvenue {user.username} !')
                
                if user.role == User.ROLE_GARAGE:
                    return redirect('accounts:dashboard_garage')
                return redirect('accounts:dashboard_client')
            else:
                messages.error(request, 'Identifiants incorrects.')
    else:
        form = CustomAuthenticationForm(request)
    
    return render(request, 'registration/login.html', {'form': form, 'page_title': 'Connexion'})


def logout_view(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, 'Déconnecté avec succès.')
    return redirect('accounts:login')


@login_required
def dashboard_client_view(request):
    """Tableau de bord client"""
    if request.user.role != User.ROLE_CLIENT and not request.user.is_superuser:
        messages.error(request, 'Accès réservé aux clients.')
        return redirect('core:home')
    
    return render(request, 'accounts/dashboard_client.html', {'page_title': 'Mon espace client'})


@login_required
def dashboard_garage_view(request):
    """Tableau de bord garage"""
    if request.user.role != User.ROLE_GARAGE and not request.user.is_superuser:
        messages.error(request, 'Accès réservé aux garages.')
        return redirect('core:home')
    
    # Récupérer le profil garage si existant
    garage = getattr(request.user, 'garage_profile', None)
    
    return render(request, 'accounts/dashboard_garage.html', {
        'page_title': 'Espace Garage',
        'garage': garage
    })


@login_required
def profile_edit_view(request):
    """Édition du profil"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour !')
            return redirect('accounts:profile_edit')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile_edit.html', {
        'form': form, 
        'page_title': 'Mon profil'
    })