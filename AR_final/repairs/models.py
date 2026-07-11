from django.db import models
from django.conf import settings


class RepairRequest(models.Model):
    STATUS_PENDING   = 'en_attente'
    STATUS_ACCEPTED  = 'acceptee'
    STATUS_IN_PROGRESS = 'en_cours'
    STATUS_DONE      = 'terminee'
    STATUS_CANCELLED = 'annulee'

    STATUS_CHOICES = [
        (STATUS_PENDING,     'En attente'),
        (STATUS_ACCEPTED,    'Acceptée'),
        (STATUS_IN_PROGRESS, 'En cours'),
        (STATUS_DONE,        'Terminée'),
        (STATUS_CANCELLED,   'Annulée'),
    ]

    TYPE_CHOICES = [
        ('entretien',    'Entretien général'),
        ('reparation',   'Réparation mécanique'),
        ('carrosserie',  'Carrosserie'),
        ('diagnostic',   'Diagnostic'),
        ('vidange',      'Vidange / Filtres'),
        ('pneumatiques', 'Pneumatiques'),
        ('electrique',   'Électrique'),
        ('autre',        'Autre'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='repair_requests',
        verbose_name='Propriétaire'
    )
    garage = models.ForeignKey(
        'garages.Garage',
        on_delete=models.CASCADE,
        related_name='repair_requests',
        verbose_name='Garage'
    )
    type_service = models.CharField(
        'Type de service', max_length=20, choices=TYPE_CHOICES, default='reparation'
    )
    vehicle_description = models.CharField(
        'Véhicule', max_length=200,
        help_text='Ex : Toyota Corolla 2015, immatriculation LT 123 A'
    )
    description = models.TextField('Description du problème')
    status = models.CharField(
        'Statut', max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    garage_note = models.TextField(
        'Note du garage', blank=True,
        help_text='Message du garage au propriétaire (raison refus, infos, etc.)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Demande de réparation'
        verbose_name_plural = 'Demandes de réparation'
        ordering = ['-created_at']

    def __str__(self):
        return f"Demande #{self.pk} – {self.owner.username} → {self.garage.name}"

    def get_status_badge(self):
        colors = {
            self.STATUS_PENDING:     'warning',
            self.STATUS_ACCEPTED:    'success',
            self.STATUS_IN_PROGRESS: 'primary',
            self.STATUS_DONE:        'dark',
            self.STATUS_CANCELLED:   'danger',
        }
        return colors.get(self.status, 'secondary')


class Appointment(models.Model):
    STATUS_PENDING   = 'en_attente'
    STATUS_CONFIRMED = 'confirme'
    STATUS_CANCELLED = 'annule'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'En attente de confirmation'),
        (STATUS_CONFIRMED, 'Confirmé'),
        (STATUS_CANCELLED, 'Annulé'),
    ]

    repair_request = models.OneToOneField(
        RepairRequest,
        on_delete=models.CASCADE,
        related_name='appointment',
        verbose_name='Demande associée'
    )
    scheduled_at = models.DateTimeField('Date et heure du rendez-vous')
    status = models.CharField(
        'Statut', max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    notes = models.TextField('Notes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        ordering = ['scheduled_at']

    def __str__(self):
        return f"RDV #{self.pk} – {self.scheduled_at.strftime('%d/%m/%Y %H:%M')}"
