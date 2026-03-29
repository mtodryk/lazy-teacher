from django.core.management.base import BaseCommand
from quizes.models import QuizSubmission

class Command(BaseCommand):
    help = "Shows the total number of quiz submissions"

    def handle(self, *args, **options):
        count = QuizSubmission.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Total submissions: {count}"))