from django.core.management.base import BaseCommand
from quizes.models import Quiz

class Command(BaseCommand):
    help = "Shows the total number of created quizes"

    def handle(self, *args, **options):
        count = Quiz.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Total quizes created: {count}"))