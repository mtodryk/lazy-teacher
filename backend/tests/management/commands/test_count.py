from django.core.management.base import BaseCommand
from tests.models import Test

class Command(BaseCommand):
    help = "Shows the total number of created tests"

    def handle(self, *args, **options):
        count = Test.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Total tests created: {count}"))