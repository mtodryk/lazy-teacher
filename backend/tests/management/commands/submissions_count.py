from django.core.management.base import BaseCommand
from tests.models import TestSubmission

class Command(BaseCommand):
    help = "Shows the total number of test submissions"

    def handle(self, *args, **options):
        count = TestSubmission.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Total submissions: {count}"))