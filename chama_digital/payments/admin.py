from django.contrib import admin
from .models import PaymentTransaction, PaymentVerification, Receipt


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('external_reference', 'member', 'payment_method', 'amount', 'status', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_type', 'chama')


@admin.register(PaymentVerification)
class PaymentVerificationAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'decision', 'verified_by', 'verified_at')


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'transaction', 'issued_at', 'email_sent', 'sms_sent')
