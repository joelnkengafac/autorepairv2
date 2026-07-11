from django.db import models

class ServiceCategory(models.Model):
    name = models.CharField("Nom du service", max_length=100)
    slug = models.SlugField("URL Slug", unique=True, help_text="Identifiant unique pour l'URL")
    icon = models.CharField("Icône (classe CSS ou emoji)", max_length=50, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class GarageService(models.Model):
    garage = models.ForeignKey('garages.Garage', on_delete=models.CASCADE, related_name='services')
    service = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    price_starting_at = models.DecimalField("Prix à partir de", max_digits=8, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = "Service de Garage"
        verbose_name_plural = "Services de Garage"
        unique_together = ('garage', 'service') # Un garage ne peut pas proposer 2 fois le même service

    def __str__(self):
        return f"{self.garage.name} - {self.service.name}"