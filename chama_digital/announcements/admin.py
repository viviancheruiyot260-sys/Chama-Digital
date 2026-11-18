from django.contrib import admin
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'chama', 'category', 'author', 'created_at')
    list_filter = ('category', 'chama')
