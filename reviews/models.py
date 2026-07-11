from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from garages.models import Garage

class Review(models.Model):
    """Avis laissé par un client sur un garage"""
    
    garage = models.ForeignKey(
        Garage, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name="Garage"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reviews',
        verbose_name="Client"
    )
    
    # Note de 1 à 5 étoiles
    rating = models.PositiveSmallIntegerField(
        "Note",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="De 1 (mécontent) à 5 (excellent)"
    )
    
    # Commentaire
    title = models.CharField(
        "Titre", 
        max_length=100, 
        blank=True,
        help_text="Résumé de votre avis (optionnel)"
    )
    comment = models.TextField(
        "Commentaire", 
        max_length=1000,
        help_text="Partagez votre expérience"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(
        "Avis vérifié", 
        default=False,
        help_text="Cochez si le client a réellement utilisé le service"
    )
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']  # Plus récents en premier
        unique_together = ['garage', 'user']  # Un client = un avis par garage
        indexes = [
            models.Index(fields=['garage', '-rating']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.garage.name} : {self.rating}/5"

    def get_star_display(self):
        """Retourne les étoiles en format texte pour l'affichage"""
        return '★' * self.rating + '☆' * (5 - self.rating)