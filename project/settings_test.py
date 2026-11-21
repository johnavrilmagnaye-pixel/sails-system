from project.settings import *


# Exercise the same database backend and PostgreSQL-specific features in tests
# that are used in production. Django creates a separate test database from
# these connection settings and prefixes its name with ``test_`` by default.
DATABASES['default'].update({
    'NAME': os.environ.get('TEST_DB_NAME', os.environ.get('DB_NAME', 'sails_crm')),
    'USER': os.environ.get('TEST_DB_USER', os.environ.get('DB_USER', 'sails_crm')),
    'PASSWORD': os.environ.get('TEST_DB_PASSWORD', os.environ.get('DB_PASSWORD', 'sails_crm')),
    'HOST': os.environ.get('TEST_DB_HOST', os.environ.get('DB_HOST', 'localhost')),
    'PORT': os.environ.get('TEST_DB_PORT', os.environ.get('DB_PORT', '5432')),
})

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

CELERY_TASK_ALWAYS_EAGER = True

# Tests render source assets directly. Production's offline compressor manifest
# is a deployment artifact and should not be required by the test suite.
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False
