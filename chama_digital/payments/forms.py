from decimal import Decimal
from django import forms
from .models import PaymentTransaction
from .services import MONTH_CHOICES


class MpesaPaymentForm(forms.Form):
    contribution_month = forms.ChoiceField(
        label='Contribution Month',
        choices=MONTH_CHOICES,
        initial='2026-11',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    amount = forms.DecimalField(
        label='Amount (KES)',
        min_value=Decimal('100.00'),
        max_digits=12,
        decimal_places=2,
        initial=Decimal('12500.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control mono-figure', 'step': '100'}),
    )
    phone_number = forms.CharField(
        label='M-Pesa Phone Number',
        max_length=25,
        widget=forms.TextInput(attrs={'class': 'form-control mono-figure', 'placeholder': '+254 712 345 678'}),
    )
    payment_method = forms.ChoiceField(
        label='M-Pesa Channel',
        choices=[
            (PaymentTransaction.PaymentMethod.MPESA_STK, 'M-Pesa STK Push (Simulated)'),
            (PaymentTransaction.PaymentMethod.MPESA_PAYBILL, 'M-Pesa Paybill (522522)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    payment_type = forms.ChoiceField(
        label='Payment Purpose',
        choices=PaymentTransaction.PaymentType.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    simulated_outcome = forms.ChoiceField(
        label='Simulated Gateway Outcome (Dev Mode)',
        choices=[
            ('SUCCESSFUL', 'Simulate Successful M-Pesa Confirmation'),
            ('FAILED', 'Simulate Failed / Cancelled M-Pesa Prompt'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    allow_additional = forms.BooleanField(
        required=False,
        label='Allow additional contribution if this month already has a contribution',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    notify_email = forms.BooleanField(
        required=False,
        initial=True,
        label='Email confirmation',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    notify_sms = forms.BooleanField(
        required=False,
        initial=True,
        label='SMS confirmation',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


class BankPaymentForm(forms.Form):
    BANK_CHOICES = [
        ('Kenya Commercial Bank (KCB)', 'Kenya Commercial Bank (KCB)'),
        ('Equity Bank Kenya', 'Equity Bank Kenya'),
        ('Co-operative Bank of Kenya', 'Co-operative Bank of Kenya'),
        ('NCBA Bank', 'NCBA Bank'),
        ('Absa Bank Kenya', 'Absa Bank Kenya'),
        ('Standard Chartered Kenya', 'Standard Chartered Kenya'),
    ]

    contribution_month = forms.ChoiceField(
        label='Contribution Month',
        choices=MONTH_CHOICES,
        initial='2026-11',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    amount = forms.DecimalField(
        label='Amount (KES)',
        min_value=Decimal('100.00'),
        max_digits=12,
        decimal_places=2,
        initial=Decimal('12500.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control mono-figure', 'step': '100'}),
    )
    bank_name = forms.ChoiceField(
        label='Bank Name',
        choices=BANK_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    payment_method = forms.ChoiceField(
        label='Bank Channel',
        choices=[
            (PaymentTransaction.PaymentMethod.BANK_TRANSFER, 'Bank Transfer (EFT / PesaLink)'),
            (PaymentTransaction.PaymentMethod.BANK_DEPOSIT, 'Bank Deposit / Standing Order'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    external_reference = forms.CharField(
        label='Bank Transaction Reference',
        max_length=80,
        widget=forms.TextInput(attrs={'class': 'form-control mono-figure', 'placeholder': 'e.g. KCB8841209'}),
    )
    payment_type = forms.ChoiceField(
        label='Payment Purpose',
        choices=PaymentTransaction.PaymentType.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    proof_of_payment = forms.FileField(
        label='Proof of Payment (Slip Photo or PDF, Optional)',
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
    )
    allow_additional = forms.BooleanField(
        required=False,
        label='Allow additional contribution if this month already has a contribution',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
