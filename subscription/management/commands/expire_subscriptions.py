"""
Commande Django : expire_subscriptions
Désactive les garages dont l'abonnement a expiré.

Usage : python manage.py expire_subscriptions
Planifier avec cron (Linux) ou Task Scheduler (Windows) :
  0 2 * * * /path/to/venv/bin/python manage.py expire_subscriptions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from subscription.models import Subscription


class Command(BaseCommand):
    help = "Expire les abonnements arrivés à échéance et désactive les garages correspondants."

    def handle(self, *args, **options):
        now = timezone.now()

        expired = Subscription.objects.filter(
            status=Subscription.STATUS_ACTIVE,
            end_date__lte=now
        ).select_related('garage')

        count = 0
        for sub in expired:
            sub.status = Subscription.STATUS_EXPIRED
            sub.save(update_fields=['status', 'updated_at'])

            # Masquer le garage
            sub.garage.is_active = False
            sub.garage.save(update_fields=['is_active'])
            count += 1

            self.stdout.write(
                self.style.WARNING(
                    f"  Expiré : {sub.garage.name} "
                    f"(abonnement #{sub.pk}, fin le {sub.end_date.strftime('%d/%m/%Y')})"
                )
            )

        if count:
            self.stdout.write(
                self.style.SUCCESS(f"\n{count} abonnement(s) expiré(s) et garage(s) désactivé(s).")
            )
        else:
            self.stdout.write(self.style.SUCCESS("Aucun abonnement expiré. Tout est à jour."))
