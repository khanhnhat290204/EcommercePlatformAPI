#!/bin/bash
set -e  # Dừng ngay nếu có lỗi

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "📂 Running migrations..."
python manage.py migrate --noinput

echo "👑 Creating superuser if not exists..."
python manage.py shell << END
from django.contrib.auth import get_user_model

User = get_user_model()
username = "admin"
email = "admin@gmail.com"
password = "Admin@123"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Superuser created.")
else:
    print("ℹ️ Superuser already exists.")
END

echo "✅ Deploy script completed!"
