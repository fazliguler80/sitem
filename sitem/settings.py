"""
Django settings for sitem project.
"""

from pathlib import Path
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'eg0$vq4p7+=pchjso2lq+u&9=d8)cn0a&h&#my=gakjo*fp-!4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# PythonAnywhere ve kendi alan adınız için ALLOWED_HOSTS
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'fazliguler80.pythonanywhere.com',
    'nokrat.com',
    'www.nokrat.com',
    'sitem-kx2q.onrender.com',
]

# CSRF ayarları
CSRF_TRUSTED_ORIGINS = [
    'https://nokrat.com',
    'https://www.nokrat.com',
]

# ========== CLOUDINARY YAPILANDIRMASI ==========
CLOUDINARY_CLOUD_NAME = "drclbvtlg"  # Cloudinary Dashboard'dan alın
CLOUDINARY_API_KEY = "248838682669782"   # Dashboard'dan alın
CLOUDINARY_API_SECRET = "qCMpFEPrg63MCJrbHsBl75FlUiM"  # Dashboard'dan alın

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET
}

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# ========== DJANGO STORAGE AYARLARI (Cloudinary için) ==========
STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.RawMediaCloudinaryStorage'
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'
    }
}

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'bina',
    'yonetim',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sitem.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'bina/templates')],
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

X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]

WSGI_APPLICATION = 'sitem.wsgi.application'

# Database - SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    BASE_DIR / 'bina' / 'static',
]

# Media files - ARTIK CLOUDINARY KULLANILIYOR
MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'  # Cloudinary kullanıldığı için yorumda

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# UTF-8 Karakter Desteği
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# E-posta Ayarları
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'site@nokrat.com'

#import dj_database_url

# Render PostgreSQL bağlantısı (GEÇİCİ - sadece migration için)
#import os
#DATABASES['default'] = dj_database_url.config(
#    default='postgresql://site_yonetim_db_gx6o_user:CPwiqbrWz0SLz7BJc0J6ovE93npcCoxI@dpg-d8m96b3sq97s73883n7g-a:5432/site_yonetim_db_gx6o',
#    conn_max_age=600
#)