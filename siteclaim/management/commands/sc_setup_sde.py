from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from ...providers import esi


class Command(BaseCommand):
    help = 'Bootstrap the Site Claim Module from SDE (FAST!)'

    def handle(self, *args, **options):
        self.stdout.write("Loading models!")
        esi.load_map_sde()
        self.stdout.write("Done!")
