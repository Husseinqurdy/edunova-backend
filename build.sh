#!/usr/bin/env bash
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️ Running shared migrations..."
python manage.py migrate_schemas --shared

echo "🗄️ Running tenant migrations..."
python manage.py migrate_schemas

echo "📁 Collecting static files..."
python manage.py collectstatic --no-input

echo "🏗️ Setting up public tenant..."
python manage.py shell << 'PYEOF'
from lms_project.models import Institution, Domain
import os

domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost')

# Create public tenant
if not Institution.objects.filter(schema_name='public').exists():
    pub = Institution(
        schema_name='public',
        name='EduNova Platform',
        registration_number='PLATFORM-001',
    )
    pub.save()
    print(f"✅ Public institution created")
else:
    pub = Institution.objects.get(schema_name='public')
    print(f"✅ Public institution exists: {pub.name}")

# Create/update domain
if not Domain.objects.filter(tenant=pub).exists():
    Domain.objects.create(domain=domain, tenant=pub, is_primary=True)
    print(f"✅ Domain created: {domain}")
else:
    d = Domain.objects.filter(tenant=pub).first()
    d.domain = domain
    d.save()
    print(f"✅ Domain updated: {domain}")

print("🎉 Setup complete!")
PYEOF
