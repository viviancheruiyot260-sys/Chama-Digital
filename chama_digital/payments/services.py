"""
Transactional payment processing, receipt PDF generation, and external
integration stubs (Safaricom M-Pesa Daraja STK Push, SMS, Email, USSD).
"""
import io
import uuid
from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from loans.models import Loan, LoanRepayment
from notifications.models import TreasurerNotification
from savings.models import Contribution, SavingsAccount
from .models import PaymentTransaction, PaymentVerification, Receipt


MONTH_CHOICES = [
    ('2026-10', 'October 2026'),
    ('2026-11', 'November 2026'),
    ('2026-12', 'December 2026'),
    ('2027-01', 'January 2027'),
    ('2027-02', 'February 2027'),
]
MONTH_LABELS = dict(MONTH_CHOICES)


def generate_reference(prefix: str) -> str:
    return f'{prefix}{uuid.uuid4().hex[:6].upper()}'


def generate_receipt_number() -> str:
    return f'RCT-{timezone.now().strftime("%Y%m")}-{uuid.uuid4().hex[:5].upper()}'


def initiate_daraja_stk_push_stub(phone_number: str, amount: Decimal, account_ref: str) -> dict:
    """
    Integration Point for Safaricom M-Pesa Daraja STK Push API.
    In production, authenticate via OAuth2 with MPESA_CONSUMER_KEY / MPESA_CONSUMER_SECRET
    and POST to /mpesa/stkpush/v1/processrequest using MPESA_SHORTCODE and MPESA_CALLBACK_URL.
    """
    return {
        'provider': 'M-Pesa Daraja STK Push (Simulated)',
        'shortcode': settings.MPESA_SHORTCODE,
        'phone': phone_number,
        'amount': str(amount),
        'account_reference': account_ref,
        'simulated': True,
    }


def dispatch_email_confirmation_stub(user, receipt: Receipt) -> bool:
    """
    Integration Point for transactional Email delivery (Django SMTP / SendGrid / SES).
    Currently uses Django's configured EMAIL_BACKEND (console in development).
    """
    try:
        send_mail(
            subject=f'Chama Digital Receipt {receipt.receipt_number}',
            message=(
                f'Hello {user.full_name},\n\n'
                f'Your payment of KES {receipt.transaction.amount:,.2f} '
                f'({receipt.transaction.contribution_month_label}) has been confirmed.\n'
                f'Receipt No: {receipt.receipt_number}\n'
                f'Reference: {receipt.transaction.external_reference}\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False


def dispatch_sms_confirmation_stub(phone_number: str, receipt: Receipt) -> bool:
    """
    Integration Point for SMS Gateway (e.g. Africa's Talking / Twilio).
    Configure SMS_API_KEY in production environment variables.
    """
    _ = (phone_number, receipt, settings.SMS_API_KEY)
    return True


def notify_treasurer_of_transaction(tx: PaymentTransaction, status_note: str) -> TreasurerNotification:
    """Creates an internal database notification for the chama's Treasurer."""
    treasurer = tx.chama.members.filter(role='TREASURER', approval_status='ACTIVE').first()
    title = (
        f'{tx.get_payment_method_display()} — '
        f'{tx.member.full_name} (KES {tx.amount:,.2f})'
    )
    message = (
        f'Member: {tx.member.full_name} ({tx.member.member_number or "Pending No."}) | '
        f'Amount: KES {tx.amount:,.2f} | '
        f'Method: {tx.get_payment_method_display()} | '
        f'Month: {tx.contribution_month_label} | '
        f'Ref: {tx.external_reference} | '
        f'Status: {status_note}'
    )
    return TreasurerNotification.objects.create(
        chama=tx.chama,
        recipient=treasurer,
        transaction=tx,
        title=title,
        message=message,
    )


@transaction.atomic
def finalize_verified_payment(tx_id: int, verifier=None, notes: str = '') -> PaymentTransaction:
    """
    Atomically confirms a PaymentTransaction, updates Contributions or LoanRepayments,
    issues a Receipt, and notifies the Treasurer. Prevents double-counting via select_for_update.
    """
    tx = PaymentTransaction.objects.select_for_update().get(pk=tx_id)
    if tx.status == PaymentTransaction.Status.SUCCESSFUL:
        return tx

    tx.status = PaymentTransaction.Status.SUCCESSFUL
    tx.verified_by = verifier
    tx.verified_at = timezone.now()
    tx.save()

    if verifier is not None:
        PaymentVerification.objects.create(
            transaction=tx,
            verified_by=verifier,
            decision=PaymentVerification.Decision.VERIFIED,
            notes=notes or 'Payment verified and posted to member account.',
        )

    account, _ = SavingsAccount.objects.get_or_create(
        member=tx.member,
        defaults={'chama': tx.chama, 'monthly_target': tx.chama.monthly_contribution},
    )

    if tx.payment_type == PaymentTransaction.PaymentType.LOAN_REPAYMENT:
        active_loan = Loan.objects.select_for_update().filter(
            member=tx.member,
            chama=tx.chama,
            status__in=[Loan.Status.DISBURSED, Loan.Status.APPROVED],
        ).first()
        if active_loan and not hasattr(tx, 'loan_repayment_record'):
            LoanRepayment.objects.create(
                loan=active_loan,
                transaction=tx,
                amount=tx.amount,
                reference=tx.external_reference,
                recorded_by=verifier or tx.member,
            )
            if active_loan.outstanding_balance <= Decimal('0.00'):
                active_loan.status = Loan.Status.COMPLETED
                active_loan.save()
    else:
        if not hasattr(tx, 'contribution_record'):
            existing_month_total = account.month_total(tx.contribution_month)
            new_total = existing_month_total + tx.amount
            contrib_status = (
                Contribution.Status.PAID
                if new_total >= account.monthly_target
                else Contribution.Status.PARTIAL
            )
            Contribution.objects.create(
                member=tx.member,
                chama=tx.chama,
                transaction=tx,
                month=tx.contribution_month,
                month_label=tx.contribution_month_label,
                amount=tx.amount,
                status=contrib_status,
            )

    receipt, created = Receipt.objects.get_or_create(
        transaction=tx,
        defaults={'receipt_number': generate_receipt_number()},
    )
    if created:
        if tx.notify_email:
            receipt.email_sent = dispatch_email_confirmation_stub(tx.member, receipt)
        if tx.notify_sms:
            receipt.sms_sent = dispatch_sms_confirmation_stub(tx.phone_number or tx.member.phone_number, receipt)
        receipt.save()

    notify_treasurer_of_transaction(tx, 'Confirmed & Receipt Issued')
    return tx


def build_receipt_pdf_bytes(receipt: Receipt) -> bytes:
    """Generates a clean PDF payment receipt using ReportLab."""
    tx = receipt.transaction
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 30 * mm
    pdf.setFillColorRGB(0.08, 0.33, 0.18)  # Forest green #14532D
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(24 * mm, y, 'CHAMA DIGITAL — OFFICIAL PAYMENT RECEIPT')

    y -= 8 * mm
    pdf.setFillColorRGB(0.37, 0.44, 0.40)
    pdf.setFont('Helvetica', 10)
    pdf.drawString(24 * mm, y, f'{tx.chama.name}  |  Invite Code: {tx.chama.invite_code}')

    y -= 6 * mm
    pdf.line(24 * mm, y, width - 24 * mm, y)

    rows = [
        ('Receipt Number', receipt.receipt_number),
        ('Member Name', tx.member.full_name),
        ('Membership Number', tx.member.member_number or 'Pending'),
        ('Contribution Month', tx.contribution_month_label),
        ('Payment Type', tx.get_payment_type_display()),
        ('Payment Method', tx.get_payment_method_display()),
        ('Transaction Reference', tx.external_reference),
        ('Payment Date', timezone.localtime(tx.created_at).strftime('%d %b %Y, %I:%M %p EAT')),
        ('Payment Status', tx.get_status_display()),
        ('Amount Paid', f'KES {tx.amount:,.2f}'),
    ]

    y -= 14 * mm
    for label, value in rows:
        pdf.setFillColorRGB(0.35, 0.42, 0.38)
        pdf.setFont('Helvetica-Bold', 10)
        pdf.drawString(24 * mm, y, f'{label}:')
        pdf.setFillColorRGB(0.09, 0.16, 0.12)
        pdf.setFont('Helvetica', 10)
        pdf.drawString(82 * mm, y, str(value))
        y -= 9 * mm

    y -= 6 * mm
    pdf.line(24 * mm, y, width - 24 * mm, y)
    y -= 10 * mm
    pdf.setFillColorRGB(0.45, 0.45, 0.45)
    pdf.setFont('Helvetica-Oblique', 9)
    sim_note = 'Simulated Development Receipt' if tx.is_simulated else 'Verified Payment Receipt'
    pdf.drawString(24 * mm, y, f'{sim_note} · Generated by Chama Digital (Django + ReportLab)')

    pdf.showPage()
    pdf.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
