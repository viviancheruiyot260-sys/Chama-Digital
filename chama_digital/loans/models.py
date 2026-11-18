from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.db import models
from django.db.models import Sum


class LoanApplication(models.Model):
    """Member loan request awaiting Chairperson / Treasurer review."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loan_applications',
    )
    chama = models.ForeignKey(
        'accounts.ChamaGroup',
        on_delete=models.CASCADE,
        related_name='loan_applications',
    )
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    repayment_months = models.PositiveIntegerField(default=6)
    purpose = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_loans',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Application #{self.pk} - {self.member.full_name} (KES {self.requested_amount})'


class Loan(models.Model):
    """Active, disbursed, or completed chama loan calculated from verified repayments."""

    class Status(models.TextChoices):
        APPROVED = 'APPROVED', 'Approved (Awaiting Disbursement)'
        DISBURSED = 'DISBURSED', 'Disbursed / Active'
        COMPLETED = 'COMPLETED', 'Completed'
        REJECTED = 'REJECTED', 'Rejected'

    application = models.OneToOneField(
        LoanApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_record',
    )
    loan_code = models.CharField(max_length=30, unique=True)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='loans',
    )
    chama = models.ForeignKey(
        'accounts.ChamaGroup',
        on_delete=models.CASCADE,
        related_name='loans',
    )
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    repayment_months = models.PositiveIntegerField(default=6)
    purpose = models.CharField(max_length=255)
    next_repayment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPROVED)
    disbursed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disbursed_loans',
    )
    disbursed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.loan_code} - {self.member.full_name}'

    @property
    def total_repaid(self) -> Decimal:
        agg = self.repayments.aggregate(total=Sum('amount'))
        return agg['total'] or Decimal('0.00')

    @property
    def outstanding_balance(self) -> Decimal:
        if self.status == self.Status.REJECTED:
            return Decimal('0.00')
        bal = self.principal_amount - self.total_repaid
        return bal if bal > Decimal('0.00') else Decimal('0.00')

    @property
    def installment_amount(self) -> Decimal:
        if not self.repayment_months:
            return self.principal_amount
        return (self.principal_amount / Decimal(self.repayment_months)).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )


class LoanRepayment(models.Model):
    """Verified repayment entry reducing a Loan's outstanding balance."""

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='repayments',
    )
    transaction = models.OneToOneField(
        'payments.PaymentTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='loan_repayment_record',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=80)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_repayments',
    )
    repaid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-repaid_at']

    def __str__(self):
        return f'{self.loan.loan_code} repayment KES {self.amount}'
