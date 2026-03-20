#!/bin/bash

set -e

echo "Waiting for PostgreSQL..."
while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${POSTGRES_HOST:-db}', ${POSTGRES_PORT:-5432}))
    s.close()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up"

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Creating admin user if not exists..."

python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")

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
        print("Creating superuser...")
        user.set_password(password)
        user.save()
        print(f"Superuser '{username}' created successfully.")
    else:
        print(f"Superuser '{username}' already exists.")
except Exception as e:
    print(f"Error creating superuser: {e}")
EOF

echo "Starting: $@"
exec "$@"
