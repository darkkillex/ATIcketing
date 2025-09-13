from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'tickets',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ATIcketing.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ATIcketing.wsgi.application'
ASGI_APPLICATION = 'ATIcketing.asgi.application'

# PostgreSQL required
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'aticketing'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': int(os.getenv('DB_PORT', '5432')),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'it-it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',   # per UI Django
        'rest_framework.authentication.TokenAuthentication',     # per client esterni
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('DRF_THROTTLE_RATE_ANON', '60/min'),
        'user': os.getenv('DRF_THROTTLE_RATE_USER', '600/min'),
    },
}

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

TICKET_DEPARTMENT_EMAILS = {
    'ICT': 'ati.ict@sivam.com',
    'WH': 'ati.magazzino@sivam.com',
    'SP': 'ati.pianoturni@sivam.com',
}

if os.getenv("EMAIL_HOST"):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- Media (allegati) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Limiti per allegati (override via env se vuoi)
ATTACHMENTS_MAX_SIZE_MB = int(os.getenv('ATTACHMENTS_MAX_SIZE_MB', '15'))  # 15 MB
ATTACHMENTS_ALLOWED_EXTENSIONS = os.getenv(
    'ATTACHMENTS_ALLOWED_EXTENSIONS',
    'pdf,jpg,jpeg,png,xlsx,docx,txt'
).split(',')

# URL base per link nelle email
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")

# Mittente di default (puoi personalizzarlo)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "ATIcketing <no-reply@local>")

# --- CORS & CSRF ---
# In DEV permettiamo tutte le origini; in PROD le limitiamo via env.
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    _cors = os.getenv('CORS_ALLOWED_ORIGINS', '')
    CORS_ALLOWED_ORIGINS = [x.strip() for x in _cors.split(',') if x.strip()]

# Se usi un frontend separato con cookie/SessionAuth su HTTPS, imposta anche i trusted origins CSRF.
# Formato richiesto da Django: include schema (http/https), es: https://intranet.local
_csrf = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _csrf:
    CSRF_TRUSTED_ORIGINS = [x.strip() for x in _csrf.split(',') if x.strip()]

# Se intendi usare cookie di sessione cross-site dal frontend (non necessario con TokenAuth):
# CORS_ALLOW_CREDENTIALS = True
# SESSION_COOKIE_SAMESITE = 'None'
# CSRF_COOKIE_SAMESITE = 'None'
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
