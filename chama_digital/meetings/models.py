from django.conf import settings
from django.db import models


class ChamaEvent(models.Model):
    """Represents chama meetings, AGMs, celebrations, and important group occasions."""

    class EventType(models.TextChoices):
        REGULAR_MEETING = 'REGULAR_MEETING', 'Regular Chama Meeting'
        AGM = 'AGM', 'Annual General Meeting'
        SPECIAL_SAVINGS = 'SPECIAL_SAVINGS', 'Special Savings Event'
        CELEBRATION = 'CELEBRATION', 'Group Celebration'
        BIRTHDAY = 'BIRTHDAY', 'Member Birthday'
        COMMUNITY = 'COMMUNITY', 'Community Activity'

    chama = models.ForeignKey(
        'accounts.ChamaGroup',
        on_delete=models.CASCADE,
        related_name='events',
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events',
    )
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        default=EventType.REGULAR_MEETING,
    )
    title = models.CharField(max_length=180)
    event_date = models.DateField()
    event_time = models.CharField(max_length=50)
    venue = models.CharField(max_length=180)
    agenda = models.TextField(blank=True)
    description = models.TextField(blank=True)
    minutes_summary = models.TextField(blank=True)
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['event_date', 'event_time']

    def __str__(self):
        return f'{self.title} ({self.event_date})'

    @property
    def is_meeting(self):
        return self.event_type in (self.EventType.REGULAR_MEETING, self.EventType.AGM)


class AttendanceRecord(models.Model):
    """Attendance tracking managed by the Chama Secretary."""

    event = models.ForeignKey(
        ChamaEvent,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    attended = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'member')

    def __str__(self):
        return f'{self.member.full_name} @ {self.event.title}'
