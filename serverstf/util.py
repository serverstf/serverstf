
from django.conf import settings

import pygeoip
geoip = pygeoip.GeoIP(settings.GEOIP_CITY_DATA)

def get_region(request):
		"""
			Yields the region identifier (ISO 3166 continent code) of a
			request. If the request comes from an authenticated user
			which has a `region` set on their model instance, that
			value is used.
			
			If not region is manually set or the user is anonymous the
			region will attempt to be deduced from the HTTP_X_FORWARDED_FOR
			and REMOTE_ADDR headers. If the region still cannot be
			determined will default to North America ("NA").
		"""
		
		if request.user.is_authenticated():
			if request.user.region is not None:
				return request.user.region
				
		x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", None)
		remote_addr = request.META.get("REMOTE_ADDR", None)
		
		print x_forwarded_for, remote_addr
		
		if x_forwarded_for:
			record = geoip.record_by_addr(x_forwarded_for.split(",")[0])
			if record:
				return record["continent"].upper()
		
		if remote_addr:
			record = geoip.record_by_addr(remote_addr)
			if record:
				return record["continent"].upper()
		
		return "NA"
		
