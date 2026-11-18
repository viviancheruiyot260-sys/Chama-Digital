from django.conf import settings
from django.db import models


class TreasurerNotification(models.Model):
    """Internal database notification dispatched to the Treasurer when payments occur."""

    chama = models.ForeignKey(
        'accounts.ChamaGroup',
        on_delete=models.CASCADE,
        related_name='treasurer_notifications',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
    )
    transaction = models.ForeignKey(
        'payments.PaymentTransaction',
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    title = models.CharField(max_length=160)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({"Read" if self.is_read else "Unread"})'
