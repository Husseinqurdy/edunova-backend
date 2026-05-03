FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Only collectstatic at build time (no DB needed)
RUN python manage.py collectstatic --no-input --settings=lms.settings || true

EXPOSE 8000

# Migrations + setup run at START time (DB is available)
CMD bash -c "python manage.py migrate_schemas --shared && \
             python manage.py migrate_schemas && \
             python manage.py shell -c \"
from lms_project.models import Institution, Domain
import os
domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost')
if not Institution.objects.filter(schema_name='public').exists():
    pub = Institution(schema_name='public', name='EduNova Platform', registration_number='PLATFORM-001')
    pub.save()
    Domain.objects.get_or_create(domain=domain, defaults={'tenant': pub, 'is_primary': True})
    print('Public tenant created')
else:
    print('Public tenant exists')
\" && \
             gunicorn lms.wsgi:application --bind 0.0.0.0:\$PORT --workers 2 --timeout 120"
