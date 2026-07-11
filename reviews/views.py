from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from garages.models import Garage
from .models import Review
from .forms import ReviewForm


def garage_reviews_partial(request, garage_pk):
    """
    Vue partielle pour charger les avis via AJAX
    (Optionnel, pour chargement dynamique)
    """
    garage = get_object_or_404(Garage, pk=garage_pk)
    reviews = garage.reviews.filter(is_verified=True).select_related('user')
    
    # Calculer la moyenne
    avg_rating = garage.reviews.aggregate(
        avg=models.Avg('rating')
    )['avg'] or 0
    
    return render(request, 'reviews/partials/reviews_list.html', {
        'garage': garage,
        'reviews': reviews,
        'average_rating': round(avg_rating, 1),
        'total_reviews': reviews.count(),
    })


@login_required
def create_review(request, garage_pk):
    """Créer un nouvel avis pour un garage"""
    
    garage = get_object_or_404(Garage, pk=garage_pk)
    
    # Vérifier que l'utilisateur est un client
    if request.user.role != 'client':
        messages.error(request, "Seuls les clients peuvent laisser un avis.")
        return redirect('garages:garage_detail', pk=garage_pk)
    
    # Vérifier que l'utilisateur n'a pas déjà noté ce garage
    if Review.objects.filter(garage=garage, user=request.user).exists():
        messages.info(request, "Vous avez déjà laissé un avis pour ce garage.")
        return redirect('garages:garage_detail', pk=garage_pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.garage = garage
            review.user = request.user
            review.save()
            
            messages.success(request, "Merci pour votre avis ! 🎉")
            return redirect('garages:garage_detail', pk=garage_pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/review_form.html', {
        'form': form,
        'garage': garage,
    })


@login_required
def edit_review(request, review_pk):
    """Modifier son propre avis"""
    
    review = get_object_or_404(Review, pk=review_pk)
    
    # Vérifier que c'est bien l'auteur qui modifie
    if review.user != request.user:
        messages.error(request, "Vous ne pouvez modifier que vos propres avis.")
        return redirect('garages:garage_detail', pk=review.garage.pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre avis a été mis à jour. ✏️")
            return redirect('garages:garage_detail', pk=review.garage.pk)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'reviews/review_form.html', {
        'form': form,
        'garage': review.garage,
        'editing': True,
    })


@login_required
@require_POST
def delete_review(request, review_pk):
    """Supprimer son propre avis (via POST pour sécurité)"""
    
    review = get_object_or_404(Review, pk=review_pk)
    
    if review.user != request.user and not request.user.is_superuser:
        messages.error(request, "Action non autorisée.")
        return redirect('garages:garage_detail', pk=review.garage.pk)
    
    garage_pk = review.garage.pk
    review.delete()
    
    messages.success(request, "Votre avis a été supprimé. 🗑️")
    return redirect('garages:garage_detail', pk=garage_pk)


# API JSON pour les notes (optionnel, pour AJAX)
def garage_rating_api(request, garage_pk):
    """Retourne les stats de notation en JSON"""
    
    garage = get_object_or_404(Garage, pk=garage_pk)
    reviews = garage.reviews.filter(is_verified=True)
    
    stats = {
        'average': round(reviews.aggregate(models.Avg('rating'))['avg'] or 0, 1),
        'total': reviews.count(),
        'distribution': {
            str(i): reviews.filter(rating=i).count() 
            for i in range(1, 6)
        }
    }
    
    return JsonResponse(stats)