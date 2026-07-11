"""
Commande Django : vérifie les abonnements expirés et désactive les garages.
À exécuter quotidiennement via cron ou Windows Task Scheduler :

    # Linux/Mac (crontab -e)
    0 2 * * * /chemin/venv/bin/python manage.py check_subscriptions

    # Windows Task Scheduler → Action :
    Program : C:\\...\\venv\\Scripts\\python.exe
    Arguments : manage.py check_subscriptions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = "Expire les abonnements dont la date de fin est dépassée."

    def handle(self, *args, **options):
        now  = timezone.now()
        subs = Subscription.objects.filter(
            status=Subscription.STATUS_ACTIVE,
            end_date__lt=now
        ).select_related('garage')

        count = subs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("Aucun abonnement expiré."))
            return

        for sub in subs:
            garage_name = sub.garage.name
            sub.expire()
            self.stdout.write(
                self.style.WARNING(f"  Expiré : {garage_name} (fin: {sub.end_date})")
            )

        self.stdout.write(
            self.style.SUCCESS(f"\n{count} abonnement(s) expiré(s) et garage(s) désactivé(s).")
        )
