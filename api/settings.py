
from django.conf import settings

API_UPDATE_TIMEOUT = getattr(settings, "API_UPDATE_TIMEOUT", 5.0)
