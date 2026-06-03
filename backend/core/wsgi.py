"""WSGI config for Breathe ESG Platform"""
import os
import sys
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_wsgi_application()

# Execute tenant assignment at startup
try:
    from django.core.management import call_command
    # Route output to stderr so it shows up immediately in Render's unified logs
    call_command('assign_tenant', stdout=sys.stderr)
except Exception as e:
    import logging
    logging.getLogger(__name__).error(f"Startup task 'assign_tenant' failed: {e}")
