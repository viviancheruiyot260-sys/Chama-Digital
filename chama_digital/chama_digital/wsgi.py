"""WSGI config for Chama Digital project."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chama_digital.settings')
application = get_wsgi_application()

from chama_digital.db_bootstrap import ensure_database_ready
ensure_database_ready()
