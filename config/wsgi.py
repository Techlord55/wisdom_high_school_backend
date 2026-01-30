# Location: .\config\wsgi.py
# Location: .\config\wsgi.py
import os
from django.core.wsgi import get_wsgi_application

# We point this to our dev settings by default
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

application = get_wsgi_application()