from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Définition des rôles possibles
    ROLE_CLIENT = 'client'
    ROLE_GARAGE = 'garage'
    ROLE_ADMIN = 'admin' # L'admin utilise aussi ce modèle mais aura des permissions spéciales
    
    ROLE_CHOICES = [
        (ROLE_CLIENT, 'Client'),
        (ROLE_GARAGE, 'Garage / Mécanicien'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_CLIENT,
        help_text="Définit si l'utilisateur est un client ou un professionnel."
    )
    
    # Champs optionnels pour la photo de profil
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"