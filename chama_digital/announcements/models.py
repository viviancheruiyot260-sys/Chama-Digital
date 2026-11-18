from django.conf import settings
from django.db import models


class Announcement(models.Model):
    """Official group announcements posted by Chairperson or Secretary."""

    class Category(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        CONTRIBUTION_REMINDER = 'CONTRIBUTION_REMINDER', 'Contribution Reminder'
        MEETING_NOTICE = 'MEETING_NOTICE', 'Meeting Notice'
        IMPORTANT_NOTICE = 'IMPORTANT_NOTICE', 'Important Notice'
        EVENT = 'EVENT', 'Event'
        EMERGENCY = 'EMERGENCY', 'Emergency Announcement'

    chama = models.ForeignKey(
        'accounts.ChamaGroup',
        on_delete=models.CASCADE,
        related_name='announcements',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_announcements',
    )
    title = models.CharField(max_length=180)
    body = models.TextField()
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_category_display()})'
