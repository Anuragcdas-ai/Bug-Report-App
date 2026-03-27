from django.contrib import admin

from .models import Bug, Profile,Sprint

admin.site.register(Bug)
admin.site.register(Sprint)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


