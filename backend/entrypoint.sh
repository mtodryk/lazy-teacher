#!/bin/bash

set -e

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if not password or not email or not username:
    print("WARNING: ADMIN CREDENTIALS not set. Skipping superuser creation.")
else:
    try:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password(password)
            user.save()
            print(f"Superuser '{username}' created successfully.")
        else:
            print(f"Superuser '{username}' already exists.")
    except Exception as e:
        print(f"Warning: Could not create superuser: {e}")
EOF

echo "Starting: $@"
exec "$@"
