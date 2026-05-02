#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate_schemas --shared
python manage.py migrate_schemas
python manage.py collectstatic --no-input

# Create public tenant if not exists
python manage.py shell << 'PYEOF'
from lms_project.models import Institution, Domain
import os

domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost')

if not Institution.objects.filter(schema_name='public').exists():
    pub = Institution(
        schema_name='public',
        name='EduNova Platform',
        registration_number='PLATFORM-001',
    )
    pub.save()
    Domain.objects.create(domain=domain, tenant=pub, is_primary=True)
    print(f"✅ Public tenant created for domain: {domain}")
else:
    print("✅ Public tenant already exists")
PYEOF
