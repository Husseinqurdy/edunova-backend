import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url
import cloudinary

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True") == "True"

RAILWAY_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
ALLOWED_HOSTS = ["*"]  # Keep open — django-tenants needs wildcard
if RAILWAY_DOMAIN:
    ALLOWED_HOSTS = ["*", RAILWAY_DOMAIN, f"*.{RAILWAY_DOMAIN}", "localhost", "127.0.0.1"]

TENANT_MODEL = "lms_project.Institution"
TENANT_DOMAIN_MODEL = "lms_project.Domain"
PUBLIC_SCHEMA_NAME = "public"
TENANT_URLCONF = "lms_project.tenant_urls"
PUBLIC_SCHEMA_URLCONF = "lms.urls"

SHARED_APPS = [
    'django_tenants',
    'lms_project',
    'core',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'cloudinary_storage',
    'cloudinary',
    'rest_framework',
    'auditlog',
]

TENANT_APPS = [
    'core',
    'django.contrib.auth',
    'django.contrib.admin',
]

INSTALLED_APPS = list(dict.fromkeys(
    SHARED_APPS + [app for app in TENANT_APPS if app not in SHARED_APPS]
))

AUTH_USER_MODEL = 'core.User'
AUTHENTICATION_BACKENDS = [
    'core.backends.StrictEmailBackend',
    'core.backends.RegistrationNumberBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Dar_es_Salaam'
USE_I18N = True
USE_TZ = True

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django_tenants.middleware.TenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lms.urls'
WSGI_APPLICATION = 'lms.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database - Railway provides DATABASE_URL automatically
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
    DATABASES['default']['ENGINE'] = 'django_tenants.postgresql_backend'
else:
    # Local development fallback
    DATABASES = {
        'default': {
            'ENGINE': 'django_tenants.postgresql_backend',
            'NAME': os.getenv('DB_NAME', 'lms_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }

DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
}
if os.getenv('CLOUDINARY_CLOUD_NAME'):
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    )
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_ROOT = BASE_DIR / 'media'

# CORS - allow Railway and Netlify
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept", "authorization", "content-type",
    "origin", "user-agent", "x-csrftoken", "x-requested-with",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ZENOPAY_API_KEY = os.getenv("ZENOPAY_API_KEY", "")

# Railway
PORT = os.getenv("PORT", "8000")

# Railway specific
PORT = os.getenv("PORT", "8000")
