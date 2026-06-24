from datetime import timedelta
from pathlib import Path
import environ
import os
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
SECRET_KEY = env.str('SECRET_KEY')
DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'rest_framework',
    'rest_framework_simplejwt',
    
    'product',
    'main',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ],
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'product.middleware.JWTCookieMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'product.middleware.RestoranMiddleware',
]
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_AGE = 86400
ROOT_URLCONF = 'Admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'Admin.wsgi.application'


from Admin.set_database import *

DATABASES = LOCAL_DATABASE

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join('static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_DIRS = [
    BASE_DIR / "staticfiles", 
]


AUTH_USER_MODEL = "main.CustomUser"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# LOGGING = {
#     'version':1,
#     'handlers':{
#          'file': {
#             'level': 'DEBUG',
#             'class': 'logging.FileHandler',
#             'filename': 'debug.log'
#         },
#         'console':{'class':'logging.StreamHandler'}
#     },
#     'loggers':{
#         'django.db.backends':{
#             'handlers':['file'],
#             'level':'DEBUG'
#                     }
#                }
# } 