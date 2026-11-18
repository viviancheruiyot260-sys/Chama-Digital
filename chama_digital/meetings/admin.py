from django.contrib import admin
from .models import AttendanceRecord, ChamaEvent


@admin.register(ChamaEvent)
class ChamaEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'event_date', 'venue', 'is_cancelled')
    list_filter = ('event_type', 'is_cancelled', 'chama')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('event', 'member', 'attended', 'recorded_at')
