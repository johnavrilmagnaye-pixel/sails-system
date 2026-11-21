import os


# Defaults suitable for both Docker and a local virtual environment. Production
# deployments can override every value without changing this file.
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '60'))
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', '300'))
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', '30'))

# Keep logs attached to the process so they are available through Docker logs
# and in the terminal during local development.
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
