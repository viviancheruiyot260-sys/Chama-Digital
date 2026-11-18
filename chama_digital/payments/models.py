from django.conf import settings
from django.db import models


class PaymentTransaction(models.Model):
    """Records M-Pesa, Bank, and USSD contribution/repayment transactions."""

    class PaymentType(models.TextChoices):
        MONTHLY_CONTRIBUTION = 'MONTHLY_CONTRIBUTION', 'Monthly Contribution'
        LOAN_REPAYMENT = 'LOAN_REPAYMENT', 'Loan Repayment'

    class PaymentMethod(models.TextChoices):
        MPESA_STK = 'MPESA_STK', 'M-Pesa STK Push (Simulated)'
        MPESA_PAYBILL = 'MPESA_PAYBILL', 'M-Pesa Paybill (522522)'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer (EFT / PesaLink)'
        BANK_DEPOSIT = 'BANK_DEPOSIT', 'Bank Deposit / Standing Order'
        USSD = 'USSD', 'USSD Payment (*384*240#)'

    class Status(models.TextChoices):
        PENDING_VERIFICATION = 'PENDING_VERIFICATION', 'Pending Treasurer Verification'
        SUCCESSFUL = 'SUCCESSFUL', 'Successful'
        FAILED = 'FAILED', 'Failed'
        REJECTED = 'REJECTED', 'Rejected'

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    chama = models.ForeignKey(
        'accounts.ChamaGroup',
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    contribution_month = models.CharField(max_length=7, help_text='YYYY-MM')
    contribution_month_label = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(
        max_length=30,
        choices=PaymentType.choices,
        default=PaymentType.MONTHLY_CONTRIBUTION,
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.MPESA_STK,
    )
    phone_number = models.CharField(max_length=25, blank=True)
    bank_name = models.CharField(max_length=120, blank=True)
    external_reference = models.CharField(max_length=80, unique=True)
    proof_of_payment = models.FileField(upload_to='payment_proofs/', blank=True, null=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING_VERIFICATION,
    )
    is_simulated = models.BooleanField(default=True)
    allow_additional = models.BooleanField(default=False)
    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments',
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.external_reference} - {self.member.full_name} (KES {self.amount})'

    @property
    def is_bank_method(self):
        return self.payment_method in (
            self.PaymentMethod.BANK_TRANSFER,
            self.PaymentMethod.BANK_DEPOSIT,
        )


class PaymentVerification(models.Model):
    """Audit record of Treasurer verification or rejection for submitted payments."""

    class Decision(models.TextChoices):
        VERIFIED = 'VERIFIED', 'Verified & Confirmed'
        REJECTED = 'REJECTED', 'Rejected'

    transaction = models.ForeignKey(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name='verifications',
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payment_verification_logs',
    )
    decision = models.CharField(max_length=20, choices=Decision.choices)
    notes = models.CharField(max_length=255, blank=True)
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-verified_at']

    def __str__(self):
        return f'{self.transaction.external_reference} -> {self.decision}'


class Receipt(models.Model):
    """Official receipt issued only after a verified successful payment."""

    transaction = models.OneToOneField(
        PaymentTransaction,
        on_delete=models.CASCADE,
        related_name='receipt',
    )
    receipt_number = models.CharField(max_length=40, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f'{self.receipt_number} ({self.transaction.member.full_name})'
