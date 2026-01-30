# Location: .\config\settings\__init__.py
# ==================== config/settings/__init__.py ====================
import os

env = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

if 'prod' in env:
    from .prod import *
else:
    from .dev import *