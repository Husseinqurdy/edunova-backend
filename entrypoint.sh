#!/bin/bash
set -e

echo "🗄️ Running migrations..."
python manage.py migrate_schemas --shared
python manage.py migrate_schemas

echo "🏗️ Setting up public tenant..."
python manage.py shell -c "
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
    Domain.objects.get_or_create(
        domain=domain,
        defaults={'tenant': pub, 'is_primary': True}
    )
    print('✅ Public tenant created:', domain)
else:
    print('✅ Public tenant already exists')
"

echo "🚀 Starting gunicorn..."
exec gunicorn lms.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
