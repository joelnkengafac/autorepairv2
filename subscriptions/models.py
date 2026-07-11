"""
Système de monétisation AutoRepair
===================================
Flux :
  1. Le garagiste choisit une formule (Plan)
  2. Il initie un paiement (Payment) via Orange Money ou MTN MoMo
  3. Le système reçoit la confirmation (webhook ou vérification manuelle)
  4. L'abonnement (Subscription) est créé/renouvelé → garage.is_active = True
  5. Un management command vérifie chaque jour les expirations
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


# ─── 1. FORMULES D'ABONNEMENT ────────────────────────────────────────────────

class Plan(models.Model):
    MONTHLY   = 'mensuel'
    QUARTERLY = 'trimestriel'
    YEARLY    = 'annuel'

    DURATION_CHOICES = [
        (MONTHLY,   'Mensuel (30 jours)'),
        (QUARTERLY, 'Trimestriel (90 jours)'),
        (YEARLY,    'Annuel (365 jours)'),
    ]

    DURATION_DAYS = {
        MONTHLY:   30,
        QUARTERLY: 90,
        YEARLY:    365,
    }

    name        = models.CharField("Nom", max_length=100)
    duration    = models.CharField(
        "Durée", max_length=15, choices=DURATION_CHOICES, unique=True
    )
    price       = models.DecimalField("Prix (XAF)", max_digits=10, decimal_places=0)
    description = models.TextField("Description des avantages", blank=True)
    is_active   = models.BooleanField("Disponible", default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Formule d'abonnement"
        verbose_name_plural = "Formules d'abonnement"
        ordering = ['price']

    def __str__(self):
        return f"{self.name} — {self.price} XAF"

    def get_duration_days(self):
        return self.DURATION_DAYS.get(self.duration, 30)


# ─── 2. ABONNEMENTS ──────────────────────────────────────────────────────────

class Subscription(models.Model):
    STATUS_ACTIVE   = 'actif'
    STATUS_EXPIRED  = 'expire'
    STATUS_PENDING  = 'en_attente'
    STATUS_CANCELLED= 'annule'

    STATUS_CHOICES = [
        (STATUS_ACTIVE,    'Actif'),
        (STATUS_EXPIRED,   'Expiré'),
        (STATUS_PENDING,   'En attente de paiement'),
        (STATUS_CANCELLED, 'Annulé'),
    ]

    garage      = models.OneToOneField(
        'garages.Garage',
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan        = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name='subscriptions'
    )
    status      = models.CharField(
        "Statut", max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    start_date  = models.DateTimeField("Début", null=True, blank=True)
    end_date    = models.DateTimeField("Expiration", null=True, blank=True)
    auto_renew  = models.BooleanField("Renouvellement auto", default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.garage.name} — {self.plan.name} ({self.get_status_display()})"

    def is_valid(self):
        """Retourne True si l'abonnement est actif et non expiré."""
        return (
            self.status == self.STATUS_ACTIVE
            and self.end_date is not None
            and self.end_date > timezone.now()
        )

    def days_remaining(self):
        """Nombre de jours restants (0 si expiré)."""
        if self.end_date and self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0

    def activate(self, plan=None):
        """
        Active ou renouvelle l'abonnement après validation du paiement.
        Si un plan est fourni, il est mis à jour.
        """
        if plan:
            self.plan = plan

        now = timezone.now()
        # Si renouvellement : on repart de la date d'expiration actuelle
        if self.status == self.STATUS_ACTIVE and self.end_date and self.end_date > now:
            self.start_date = self.end_date
        else:
            self.start_date = now

        self.end_date = self.start_date + timedelta(days=self.plan.get_duration_days())
        self.status   = self.STATUS_ACTIVE
        self.save()

        # Activer le garage sur la plateforme
        self.garage.is_active = True
        self.garage.save(update_fields=['is_active'])

    def expire(self):
        """Désactive l'abonnement et masque le garage."""
        self.status = self.STATUS_EXPIRED
        self.save(update_fields=['status'])
        self.garage.is_active = False
        self.garage.save(update_fields=['is_active'])


# ─── 3. PAIEMENTS ────────────────────────────────────────────────────────────

class Payment(models.Model):
    # Opérateurs Mobile Money disponibles au Cameroun
    ORANGE_MONEY = 'orange_money'
    MTN_MOMO     = 'mtn_momo'
    MANUAL       = 'virement_manuel'

    PROVIDER_CHOICES = [
        (ORANGE_MONEY, 'Orange Money'),
        (MTN_MOMO,     'MTN Mobile Money'),
        (MANUAL,       'Virement / Dépôt manuel'),
    ]

    STATUS_PENDING   = 'en_attente'
    STATUS_SUCCESS   = 'succes'
    STATUS_FAILED    = 'echec'
    STATUS_REFUNDED  = 'rembourse'

    STATUS_CHOICES = [
        (STATUS_PENDING,  'En attente'),
        (STATUS_SUCCESS,  'Succès'),
        (STATUS_FAILED,   'Échec'),
        (STATUS_REFUNDED, 'Remboursé'),
    ]

    subscription   = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name='payments'
    )
    plan           = models.ForeignKey(
        Plan, on_delete=models.PROTECT, related_name='payments'
    )
    amount         = models.DecimalField("Montant (XAF)", max_digits=10, decimal_places=0)
    provider       = models.CharField(
        "Opérateur", max_length=20, choices=PROVIDER_CHOICES
    )
    phone_number   = models.CharField(
        "Numéro Mobile Money", max_length=20,
        help_text="Numéro ayant effectué le paiement (ex: 6XXXXXXXX)"
    )
    # Référence retournée par l'opérateur ou saisie manuellement
    reference      = models.CharField(
        "Référence transaction", max_length=100, blank=True, unique=True, null=True
    )
    status         = models.CharField(
        "Statut", max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    initiated_at   = models.DateTimeField("Initié le", auto_now_add=True)
    confirmed_at   = models.DateTimeField("Confirmé le", null=True, blank=True)
    # Notes internes (admin, raison d'échec, etc.)
    admin_notes    = models.TextField("Notes admin", blank=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-initiated_at']

    def __str__(self):
        return (
            f"Paiement #{self.pk} — {self.amount} XAF "
            f"({self.get_provider_display()}) — {self.get_status_display()}"
        )

    def confirm(self, reference='', admin_notes=''):
        """
        Valide manuellement le paiement (par l'admin).
        Active ensuite l'abonnement du garage.
        """
        self.status       = self.STATUS_SUCCESS
        self.confirmed_at = timezone.now()
        if reference:
            self.reference = reference
        if admin_notes:
            self.admin_notes = admin_notes
        self.save()

        # Activer / renouveler l'abonnement
        self.subscription.activate(plan=self.plan)

    def reject(self, reason=''):
        """Rejette le paiement (doublon, numéro invalide, etc.)."""
        self.status      = self.STATUS_FAILED
        self.admin_notes = reason
        self.save(update_fields=['status', 'admin_notes'])
