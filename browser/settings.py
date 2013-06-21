
from django.conf import settings

import datetime

SERVER_UPDATE_TD_INFO = datetime.timedelta(**getattr(settings, "SERVER_UPDATE_TD_INFO", {"seconds": 0}))
SERVER_UPDATE_TD_RULES = datetime.timedelta(**getattr(settings, "SERVER_UPDATE_TD_RULES", {"seconds": 0}))
SERVER_UPDATE_TD_ONLINE = datetime.timedelta(**getattr(settings, "SERVER_UPDATE_TD_ONLINE", {"seconds": 0}))
GEOIP_CITY_DATA = settings.GEOIP_CITY_DATA
