
from django.contrib import admin
from steam_auth.models import User

class UserAdmin(admin.ModelAdmin):
	
	readonly_fields = ["profile_name"]

admin.site.register(User, UserAdmin)

