from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Shows the total number of registered users."

    def handle(self, *args, **options):
        User = get_user_model()
        count = User.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Total registered users: {count}"))