from django.contrib import admin
from .models import TreasurerNotification


@admin.register(TreasurerNotification)
class TreasurerNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'chama', 'is_read', 'created_at')
    list_filter = ('is_read', 'chama')
