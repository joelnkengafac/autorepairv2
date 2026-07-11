from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Plan(models.Model):
    """Formules d'abonnement disponibles."""

    MONTHLY   = 'mensuel'
    QUARTERLY = 'trimestriel'
    ANNUAL    = 'annuel'

    PERIOD_CHOICES = [
        (MONTHLY,   'Mensuel'),
        (QUARTERLY, 'Trimestriel'),
        (ANNUAL,    'Annuel'),
    ]

    name        = models.CharField('Nom', max_length=50)
    period      = models.CharField('Période', max_length=15, choices=PERIOD_CHOICES, unique=True)
    price       = models.DecimalField('Prix (FCFA)', max_digits=10, decimal_places=0)
    duration_days = models.PositiveIntegerField('Durée (jours)')
    description = models.TextField('Description', blank=True)
    is_active   = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Formule'
        verbose_name_plural = 'Formules'
        ordering = ['price']

    def __str__(self):
        return f"{self.name} — {self.price} FCFA"


class Subscription(models.Model):
    """Abonnement d'un garage."""

    STATUS_PENDING  = 'en_attente'
    STATUS_ACTIVE   = 'actif'
    STATUS_EXPIRED  = 'expire'
    STATUS_CANCELED = 'annule'

    STATUS_CHOICES = [
        (STATUS_PENDING,  'En attente de paiement'),
        (STATUS_ACTIVE,   'Actif'),
        (STATUS_EXPIRED,  'Expiré'),
        (STATUS_CANCELED, 'Annulé'),
    ]

    garage      = models.ForeignKey(
        'garages.Garage', on_delete=models.CASCADE,
        related_name='subscriptions', verbose_name='Garage'
    )
    plan        = models.ForeignKey(
        Plan, on_delete=models.PROTECT,
        related_name='subscriptions', verbose_name='Formule'
    )
    status      = models.CharField(
        'Statut', max_length=15,
        choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    start_date  = models.DateTimeField('Début', null=True, blank=True)
    end_date    = models.DateTimeField('Expiration', null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.garage.name} — {self.plan.name} [{self.get_status_display()}]"

    def activate(self):
        """Active l'abonnement après confirmation du paiement."""
        self.status     = self.STATUS_ACTIVE
        self.start_date = timezone.now()
        self.end_date   = timezone.now() + timedelta(days=self.plan.duration_days)
        self.save()
        # Rendre le garage visible
        self.garage.is_active = True
        self.garage.save(update_fields=['is_active'])

    def is_valid(self):
        return self.status == self.STATUS_ACTIVE and self.end_date > timezone.now()

    @property
    def days_remaining(self):
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(delta.days, 0)
        return 0


class Payment(models.Model):
    """Enregistrement d'un paiement Mobile Money."""

    METHOD_ORANGE = 'orange_money'
    METHOD_MTN    = 'mtn_momo'

    METHOD_CHOICES = [
        (METHOD_ORANGE, 'Orange Money'),
        (METHOD_MTN,    'MTN Mobile Money'),
    ]

    STATUS_PENDING   = 'en_attente'
    STATUS_COMPLETED = 'valide'
    STATUS_FAILED    = 'echoue'
    STATUS_REFUNDED  = 'rembourse'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'En attente'),
        (STATUS_COMPLETED, 'Validé'),
        (STATUS_FAILED,    'Échoué'),
        (STATUS_REFUNDED,  'Remboursé'),
    ]

    subscription    = models.ForeignKey(
        Subscription, on_delete=models.CASCADE,
        related_name='payments', verbose_name='Abonnement'
    )
    amount          = models.DecimalField('Montant (FCFA)', max_digits=10, decimal_places=0)
    method          = models.CharField(
        'Moyen de paiement', max_length=20, choices=METHOD_CHOICES
    )
    phone_number    = models.CharField('Numéro Mobile Money', max_length=20)
    status          = models.CharField(
        'Statut', max_length=15,
        choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    # Référence retournée par l'opérateur (Orange/MTN)
    operator_ref    = models.CharField(
        'Référence opérateur', max_length=100, blank=True
    )
    # Référence interne unique
    reference       = models.CharField(
        'Référence interne', max_length=50, unique=True
    )
    confirmed_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='confirmed_payments',
        verbose_name='Confirmé par'
    )
    confirmed_at    = models.DateTimeField('Confirmé le', null=True, blank=True)
    notes           = models.TextField('Notes admin', blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} — {self.amount} FCFA [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        if not self.reference:
            import uuid
            self.reference = f"AR-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
