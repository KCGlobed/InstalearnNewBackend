import os
import environ
from datetime import timedelta
from pathlib import Path
env = environ.Env()
environ.Env.read_env()


ENV = os.getenv('DJANGO_ENV', 'dev')
BASE_DIR = Path(__file__).resolve().parent.parent

if ENV == 'prod':
    environ.Env.read_env(os.path.join(BASE_DIR, '.env.prod'))
else:
    environ.Env.read_env(os.path.join(BASE_DIR, '.env.dev'))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', "instalearnnewbackend-114109844441.asia-south1.run.app","instalearn-610747130982.asia-south1.run.app"])

CSRF_TRUSTED_ORIGINS = ["https://instalearnnewbackend-114109844441.asia-south1.run.app","https://instalearn-610747130982.asia-south1.run.app"]

ADMIN_URL = "https://instalearnnewbackend-114109844441.asia-south1.run.app"
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework',
    'drf_yasg',
    'simple_history',
    "rest_framework_api",
    "drf_standardized_errors",
    'rolepermissions',
    'import_export',
    "django_celery_results",
    'django_celery_beat',
    "users",
    "subscription",
    "courses",
    "user_study",
    "instructor",
    "cms",
    "assessment",
    "questions",
    "forums",
    "adminpanel.authentication",
    "adminpanel.layout",
    "adminpanel.course_app"
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'mini_lms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'mini_lms.context_processors.global_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'mini_lms.wsgi.application'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 465
EMAIL_USE_SSL = True

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("DB_NAME"),
        'USER': env("DB_USER"),
        'PASSWORD': env("DB_PASSWORD"),
        'HOST': env("DB_HOST"),
        'PORT': env("DB_PORT"),
        "CONN_MAX_AGE": 600,  
    }
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
       'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'mini_lms.pagination.CustomPageNumberPagination',
    "EXCEPTION_HANDLER": "drf_standardized_errors.handler.exception_handler",
    'PAGE_SIZE': 20,
}

DRF_STANDARDIZED_ERRORS = {
    "EXCEPTION_FORMATTER_CLASS": "mini_lms.exception_formatter.CustomExceptionFormatter",
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

ROLEPERMISSIONS_MODULE = 'mini_lms.roles'


# Static files (CSS, JavaScript, Images)
from google.oauth2 import service_account
import json
import os

creds_raw = env("GOOGLE_CREDENTIALS_JSON")

if creds_raw:
    # 1. Parse the string into a dict
    creds_dict = json.loads(creds_raw)
    
    # 2. Use .from_service_account_info() for dictionaries
    GS_CREDENTIALS = service_account.Credentials.from_service_account_info(creds_dict)
else:
    GS_CREDENTIALS = None


STORAGES = {
    "default": {
        "BACKEND": 'mini_lms.gcloud.Media',
    },
    "staticfiles": {
        "BACKEND": 'mini_lms.gcloud.Static',
    },
}

GS_BUCKET_NAME = 'instalearn-public-bucket'
GS_BUCKET_NAME_2 = 'instalearn-private-bucket'
GS_STATIC_BUCKET_NAME = 'instalearn-public-bucket'
GS_FILE_OVERWRITE = False
MEDIA_ROOT = "media/"
STATIC_ROOT = "static/"
STATIC_URL = 'https://storage.googleapis.com/{}/static/'.format(GS_STATIC_BUCKET_NAME)
MEDIA_URL = 'https://storage.googleapis.com/{}/media/'.format(GS_BUCKET_NAME)
SECURE_MEDIA_URL = 'https://storage.googleapis.com/{}/media/'.format(GS_BUCKET_NAME_2)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=2),

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
}

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "https://instalearn-website.web.app",
    "https://kcglobed-instalearn-adminpanel.web.app"
]

BASE_URL = "http://localhost:5173"
ADMIN_BASE_URL = "http://localhost:3000"

# Google credentials from Google Cloud Console
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '187256667857-h90u4bc75ep3c7vlgihsludue2vimuco.apps.googleusercourses.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'YOUR_GOOGLE_CLIENT_SECRET'

# Facebook credentials from Facebook for Developers
SOCIAL_AUTH_FACEBOOK_KEY = 'YOUR_FACEBOOK_APP_ID'
SOCIAL_AUTH_FACEBOOK_SECRET = 'YOUR_FACEBOOK_APP_SECRET'
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'id, name, email, picture.type(large)'
}


CELERY_BROKER_URL = "redis://127.0.0.1:6379",
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
timezone = "Asia/Kolkata"
CELERY_RESULT_BACKEND = "django-db"
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

from celery.schedules import crontab

GS_PROJECT_ID="kcg-newinstalearn"

CELERY_BEAT_SCHEDULE = {
    'check-and-generate-video-caption': {
        'task': 'subscription.tasks.generate_video_caption',  # Path to your task function
        'schedule': crontab(hour=1), 
        'args': (),  # Optional arguments for the task
        'kwargs': {}, # Optional keyword arguments
    }
}
