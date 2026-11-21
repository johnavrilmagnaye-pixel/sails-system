import os
import sys

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PROJECT_PATH, 'apps'))


DEBUG = os.environ.get('DEBUG', '').strip().lower() in {'1', 'true', 'yes', 'on'}


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def env_list(name, default=''):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]

SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', '')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', SUPPORT_EMAIL)
ADMINS = (('Sails CRM', ADMIN_EMAIL or SUPPORT_EMAIL),) if ADMIN_EMAIL or SUPPORT_EMAIL else ()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sails-crm'),
        'USER': os.environ.get('DB_USER', 'sails-crm'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

REDIS_BACKEND = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
REDIS_CACHE_BACKEND = os.environ.get('REDIS_CACHE_URL', 'redis://127.0.0.1:6379/1')


CONN_MAX_AGE = None

TIME_ZONE = os.environ.get('TIME_ZONE', 'UTC')
LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'en')
LANGUAGES = (
    ('en', 'English'),
    ('ru', 'Russian'),
)
LOCALE_PATHS = (os.path.join(PROJECT_PATH, 'locale'),)
SITE_ID = 1
USE_I18N = True
USE_TZ = True

DATE_INPUT_FORMATS = [
    '%Y-%m-%d',
    '%d.%m.%Y',
]
DATETIME_INPUT_FORMATS = [
    '%Y-%m-%d %H:%M',
    '%d.%m.%Y %H:%M',
]

MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(PROJECT_PATH, 'staticroot')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, 'static/assets/'),
    ('img', os.path.join(PROJECT_PATH, 'static/img/')),
    ('libs', os.path.join(PROJECT_PATH, 'static/libs/')),
    ('patches', os.path.join(PROJECT_PATH, 'static/patches')),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
)

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

SECRET_KEY = os.environ.get('SECRET_KEY', 'unsafe-development-key')

SESSION_COOKIE_DOMAIN = None

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_PATH, 'templates/'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                # 'django.template.context_processors.media',
                # 'django.template.context_processors.static',
                # 'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.AccountMiddleware',
    'accounts.middleware.LanguageMiddleware',
    'accounts.middleware.TimezoneMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '*' if DEBUG else 'localhost')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Safe defaults remain convenient for local HTTP development. Production
# deployments behind the bundled Caddy proxy enable these options through env.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', not DEBUG)
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', False)
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS')
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD')
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

ROOT_URLCONF = 'crm.urls'
DEFAULT_PROTOCOL = 'http'
DEFAULT_DOMAIN = 'localhost'

# WhiteNoise discovers static files when the application starts, so compressed
# bundles must not be generated lazily by a request. Development serves the
# source files directly; production uses bundles generated by `manage.py compress`.
COMPRESS_ENABLED = not DEBUG
COMPRESS_OFFLINE = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
]
COMPRESS_JS_FILTERS = []

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_CACHE_BACKEND,
    }
}

LOGIN_URL = '/'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.CaseInsensitiveModelBackend',
]

WSGI_APPLICATION = 'project.wsgi.application'

TEST_RUNNER = 'project.test_runner.ProjectDiscoverRunner'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'compressor',
    'django_filters',
    'timezone_field',
    'widget_tweaks',
    'rest_framework',
    'django_extensions',

    'core',
    'accounts',
    'crm',
    'notifications',
)

# set smtp settings to send emails, fallback to console if not configured
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
    if EMAIL_HOST
    else 'django.core.mail.backends.console.EmailBackend'
)

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
FROM_EMAIL = {
    'welcome': os.environ.get('WELCOME_FROM_EMAIL') or DEFAULT_FROM_EMAIL,
    'notify': os.environ.get('NOTIFY_FROM_EMAIL') or DEFAULT_FROM_EMAIL,
    'remind': os.environ.get('REMIND_FROM_EMAIL') or DEFAULT_FROM_EMAIL,
}
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)

APP_URL = os.environ.get('APP_URL', '{}://{}'.format(DEFAULT_PROTOCOL, DEFAULT_DOMAIN))

# CRM

CLEAN_ARCHIVED_ITEMS_DAYS = 60

CONTACTS_IMPORT_DATA_EXPIRE = 86400  # 1 day

TOTAL_UPLOADS_LIMIT_GB = 8
TOTAL_UPLOADS_LIMIT = TOTAL_UPLOADS_LIMIT_GB * 1024 * 1024 * 1024
UPLOAD_FILE_MAX_SIZE_MB = 20
UPLOAD_FILE_MAX_SIZE = UPLOAD_FILE_MAX_SIZE_MB * 1024 * 1024


# Rest framework

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
        'accounts.rest_permissions.AccountObjectPermission',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        # 'rest_framework.filters.DjangoFilterBackend',
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter'
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.PageNumberPagination',
    'DATE_INPUT_FORMATS': ('iso-8601', '%d.%m.%Y'),
    'ORDERING_PARAM': 'sorting',
}


LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO').upper()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name}: {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'core.utils.InternalErrorHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'asyncio': {
            'level': 'WARNING',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'WARNING',
            'propagate': True,
        },
    },
}


from project.celeryconfig.main import *

try:
    from project.settings_local import *
except ImportError:
    pass

try:
    from project.settings_local import modify
    modify(globals())
except ImportError:
    pass
