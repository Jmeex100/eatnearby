from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your_secret_key_here'

DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',       # Localhost
    'localhost',       # Localhost
    '192.168.119.40',      # Your local IP address
    '0.0.0.0',         # For binding to all network interfaces (optional)
    '192.168.43.172',   # GUEST
  'd31c-45-215-255-168.ngrok-free.app',  # Your ngrok domain
    '10.0.23.179',
    '192.168.1.189',# SCHOOL WIFI
    #  'django_extensions',  # Add this
    
    
]


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sim',
    'auths',
    'cart',
     'superadmin.apps.SuperadminConfig',
    'payments.apps.PaymentsConfig',
    'paypal.standard.ipn',
    'pwa',
    'staffs.apps.StaffsConfig', 
    'community',

]

# Session settings (recommended)
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True

# Add PWA settings at the bottom
PWA_APP_NAME = 'Eat Nearby'
PWA_APP_DESCRIPTION = "Find and order food from nearby restaurants"
PWA_APP_THEME_COLOR = '#000000'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {
        'src': '/static/images/icon-192x192.png',
        'sizes': '192x192',
        'type': 'image/png'
    },
    {
        'src': '/static/images/icon-512x512.png',
        'sizes': '512x512',
        'type': 'image/png'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/images/splash.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static', 'js', 'service-worker.js')

AUTH_USER_MODEL = 'auths.User'  # Replace 'auths' with your app name

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'core.urls'

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
                'payments.context_processors.order_notifications',
                 'staffs.context_processors.staff_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "sim/static",
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'mulangarichard1000@gmail.com'
EMAIL_HOST_PASSWORD = 'ybtz vfzn fnfr cfgq'

#  paypay settings
PAYPAL_TEST = True
PAYPAL_RECEIVER_EMAIL = 'eatnearby@gmail.com'


PAYPAL_BUY_BUTTON_IMAGE = 'https://www.paypalobjects.com/webstatic/en_US/i/buttons/checkout-logo-large.png'
PAYPAL_IDENTITY_TOKEN = 'your_sandbox_identity_token'  # Optional, for PDT if needed


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
# Pesapal settings
PESAPAL_CONSUMER_KEY = 'Ypnpr3qhC4iGX3gr1WpaGToTkHRq109D'
PESAPAL_CONSUMER_SECRET = 'bTM6fdxYWtuKoDGoA218hcZZmo0='
PESAPAL_TEST = True
PESAPAL_API_URL = 'https://demo.pesapal.com' if PESAPAL_TEST else 'https://www.pesapal.com'

# Stripe settings
STRIPE_PUBLISHABLE_KEY = 'pk_test_51R35gE03BiiFlMW7kyJ17cu21AAjuPZtj5cxVGSAwMikLLqs35syK5jOjgEc0bJeEGK38ufvyJqKUqbo486catoQ00lrrp8XDg'
STRIPE_SECRET_KEY = 'sk_test_51R35gE03BiiFlMW7mekLfURkjve5GCdE52jKv3Qv9EJaup84TnPeTGSCFZAg2lB5DZXURIg0VSlgZSapVSmimaoA00s5LsrbxM'

# Mobile money settings
AIRTEL_API_KEY = 'dummy_key'
AIRTEL_API_SECRET = 'dummy_secret'

ZAMTEL_API_KEY = 'dummy_key'
ZAMTEL_API_SECRET = 'dummy_secret'

MTN_SUBSCRIPTION_KEY = 'dummy_key'
MTN_CALLBACK_HOST = 'http://localhost:8000'

# Twilio Configuration
TWILIO_ACCOUNT_SID = 'AC82fd9f51a19dc28febd379fe64fe4e57'
TWILIO_AUTH_TOKEN = '2bd58a7286c569902174c81c79c16fbe'
TWILIO_PHONE_NUMBER = '+19897873604'
TWILIO_ENABLED = True