from django.contrib import admin
from browser.models import Network, Server, ActivityLog

admin.site.register(Network)
admin.site.register(Server)
admin.site.register(ActivityLog)
