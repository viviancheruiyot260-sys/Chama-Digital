from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum


class SavingsAccount(models.Model):
    """Individual financial account for an approved chama member."""

    member = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='savings_account',
    )
    chama = models.ForeignKey(
        'accounts.ChamaGroup',
        on_delete=models.CASCADE,
        related_name='savings_accounts',
    )
    monthly_target = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('12500.00'),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['member__full_name']

    def __str__(self):
        return f'SavingsAccount({self.member.full_name})'

    @property
    def total_savings(self) -> Decimal:
        agg = Contribution.objects.filter(member=self.member).aggregate(total=Sum('amount'))
        return agg['total'] or Decimal('0.00')

    @property
    def total_contributions_count(self) -> int:
        return Contribution.objects.filter(member=self.member).count()

    def month_total(self, month_code: str) -> Decimal:
        agg = Contribution.objects.filter(member=self.member, month=month_code).aggregate(total=Sum('amount'))
        return agg['total'] or Decimal('0.00')

    def has_paid_month(self, month_code: str) -> bool:
        return self.month_total(month_code) >= self.monthly_target


class Contribution(models.Model):
    """Verified contribution ledger entry linked to a confirmed PaymentTransaction."""

    class Status(models.TextChoices):
        PAID = 'PAID', 'Paid'
        PARTIAL = 'PARTIAL', 'Partially Paid'

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contributions',
    )
    chama = models.ForeignKey(
        'accounts.ChamaGroup',
        on_delete=models.CASCADE,
        related_name='contributions',
    )
    transaction = models.OneToOneField(
        'payments.PaymentTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contribution_record',
    )
    month = models.CharField(max_length=7, help_text='Format YYYY-MM')
    month_label = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PAID)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.member.full_name} - {self.month_label}: KES {self.amount}'
