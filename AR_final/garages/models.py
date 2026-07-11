from django.db import models
from django.conf import settings

class Garage(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='garage_profile'
    )
    name = models.CharField("Nom du Garage", max_length=255)
    description = models.TextField("Description", blank=True)
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    address = models.CharField("Adresse complète", max_length=255)
    city = models.CharField("Ville", max_length=100)
    zip_code = models.CharField("Code postal", max_length=10)
    
    # ⚠️ CE CHAMP DOIT EXISTER
    phone_number = models.CharField("Téléphone", max_length=15, blank=True)
    
    website = models.URLField(blank=True, null=True)
    is_open = models.BooleanField("Ouvert actuellement", default=True)
    opening_hours = models.TextField("Horaires d'ouverture")
    
    logo = models.ImageField(upload_to='garages/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='garages/banners/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Garage"
        verbose_name_plural = "Garages"

    def __str__(self):
        return self.name