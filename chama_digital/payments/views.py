import csv
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from accounts.permissions import active_chama_member_required, role_required
from loans.models import Loan
from notifications.models import TreasurerNotification
from savings.models import Contribution, SavingsAccount
from .forms import BankPaymentForm, MpesaPaymentForm
from .models import PaymentTransaction, PaymentVerification, Receipt
from .services import (
    MONTH_LABELS,
    build_receipt_pdf_bytes,
    finalize_verified_payment,
    generate_reference,
    initiate_daraja_stk_push_stub,
    notify_treasurer_of_transaction,
)


@role_required(User.Role.MEMBER)
def make_payment_view(request):
    """Member payment page supporting Simulated M-Pesa STK Push and Treasurer-verified Bank Payments."""
    chama = request.user.chama
    account, _ = SavingsAccount.objects.get_or_create(
        member=request.user,
        defaults={'chama': chama, 'monthly_target': chama.monthly_contribution},
    )
    active_tab = request.GET.get('method', 'mpesa')
    mpesa_form = MpesaPaymentForm(initial={'phone_number': request.user.phone_number, 'amount': account.monthly_target})
    bank_form = BankPaymentForm(initial={'amount': account.monthly_target})

    if request.method == 'POST':
        channel_group = request.POST.get('channel_group', 'mpesa')
        if channel_group == 'mpesa':
            active_tab = 'mpesa'
            mpesa_form = MpesaPaymentForm(request.POST)
            if mpesa_form.is_valid():
                month = mpesa_form.cleaned_data['contribution_month']
                month_label = MONTH_LABELS.get(month, month)
                payment_type = mpesa_form.cleaned_data['payment_type']
                allow_additional = mpesa_form.cleaned_data['allow_additional']

                if (
                    payment_type == PaymentTransaction.PaymentType.MONTHLY_CONTRIBUTION
                    and account.has_paid_month(month)
                    and not allow_additional
                ):
                    messages.warning(
                        request,
                        f'{month_label} contribution is already paid. Check "Allow additional contribution" to add an extra deposit.',
                    )
                else:
                    outcome = mpesa_form.cleaned_data['simulated_outcome']
                    ref = generate_reference('SK')
                    initiate_daraja_stk_push_stub(
                        mpesa_form.cleaned_data['phone_number'],
                        mpesa_form.cleaned_data['amount'],
                        request.user.member_number or request.user.phone_number,
                    )
                    with transaction.atomic():
                        tx = PaymentTransaction.objects.create(
                            member=request.user,
                            chama=chama,
                            contribution_month=month,
                            contribution_month_label=month_label,
                            amount=mpesa_form.cleaned_data['amount'],
                            payment_type=payment_type,
                            payment_method=mpesa_form.cleaned_data['payment_method'],
                            phone_number=mpesa_form.cleaned_data['phone_number'],
                            external_reference=ref,
                            status=(
                                PaymentTransaction.Status.PENDING_VERIFICATION
                                if outcome == 'SUCCESSFUL'
                                else PaymentTransaction.Status.FAILED
                            ),
                            is_simulated=True,
                            allow_additional=allow_additional,
                            notify_email=mpesa_form.cleaned_data['notify_email'],
                            notify_sms=mpesa_form.cleaned_data['notify_sms'],
                        )
                        if outcome == 'SUCCESSFUL':
                            finalize_verified_payment(tx.pk, verifier=None, notes='Simulated M-Pesa STK callback confirmation')
                            messages.success(
                                request,
                                f'Simulated M-Pesa payment confirmed (Ref: {ref}). Your savings balance has been updated and the Treasurer has been notified.',
                            )
                            return redirect('payments:receipt_detail', receipt_id=tx.receipt.pk)
                        else:
                            messages.error(
                                request,
                                f'Simulated M-Pesa payment failed (Ref: {ref}). Your savings balance was not modified.',
                            )
        elif channel_group == 'bank':
            active_tab = 'bank'
            bank_form = BankPaymentForm(request.POST, request.FILES)
            if bank_form.is_valid():
                month = bank_form.cleaned_data['contribution_month']
                month_label = MONTH_LABELS.get(month, month)
                payment_type = bank_form.cleaned_data['payment_type']
                allow_additional = bank_form.cleaned_data['allow_additional']
                ref = bank_form.cleaned_data['external_reference'].strip().upper()

                if PaymentTransaction.objects.filter(external_reference__iexact=ref).exists():
                    messages.error(request, f'Transaction reference {ref} has already been submitted.')
                elif (
                    payment_type == PaymentTransaction.PaymentType.MONTHLY_CONTRIBUTION
                    and account.has_paid_month(month)
                    and not allow_additional
                ):
                    messages.warning(
                        request,
                        f'{month_label} contribution is already paid. Check "Allow additional contribution" to submit an extra deposit.',
                    )
                else:
                    with transaction.atomic():
                        tx = PaymentTransaction.objects.create(
                            member=request.user,
                            chama=chama,
                            contribution_month=month,
                            contribution_month_label=month_label,
                            amount=bank_form.cleaned_data['amount'],
                            payment_type=payment_type,
                            payment_method=bank_form.cleaned_data['payment_method'],
                            phone_number=request.user.phone_number,
                            bank_name=bank_form.cleaned_data['bank_name'],
                            external_reference=ref,
                            proof_of_payment=bank_form.cleaned_data.get('proof_of_payment'),
                            status=PaymentTransaction.Status.PENDING_VERIFICATION,
                            is_simulated=True,
                            allow_additional=allow_additional,
                        )
                        notify_treasurer_of_transaction(tx, 'Awaiting Treasurer Bank Verification')
                    messages.info(
                        request,
                        f'Bank payment (Ref: {ref}) submitted for Treasurer verification. Your balance will update once the Treasurer confirms the deposit.',
                    )
                    return redirect('payments:payment_history')

    return render(request, 'payments/make_payment.html', {
        'mpesa_form': mpesa_form,
        'bank_form': bank_form,
        'active_tab': active_tab,
        'chama': chama,
        'account': account,
    })


@role_required(User.Role.MEMBER)
def payment_history_view(request):
    status_filter = request.GET.get('status', 'ALL')
    transactions = PaymentTransaction.objects.filter(
        member=request.user,
        chama=request.user.chama,
    ).select_related('receipt')
    if status_filter != 'ALL':
        transactions = transactions.filter(status=status_filter)

    return render(request, 'payments/payment_history.html', {
        'transactions': transactions,
        'status_filter': status_filter,
        'status_choices': PaymentTransaction.Status.choices,
    })


@active_chama_member_required
def receipt_detail_view(request, receipt_id):
    receipt = get_object_or_404(
        Receipt.objects.select_related('transaction', 'transaction__member', 'transaction__chama'),
        pk=receipt_id,
    )
    tx = receipt.transaction
    if tx.chama != request.user.chama:
        messages.error(request, 'Access denied for receipts outside your Chama.')
        return redirect(request.user.get_dashboard_url_name())
    if tx.member != request.user and not request.user.is_official:
        messages.error(request, 'You may only view your own payment receipts.')
        return redirect(request.user.get_dashboard_url_name())

    return render(request, 'payments/receipt_detail.html', {'receipt': receipt, 'tx': tx})


@active_chama_member_required
def receipt_pdf_view(request, receipt_id):
    receipt = get_object_or_404(
        Receipt.objects.select_related('transaction', 'transaction__member', 'transaction__chama'),
        pk=receipt_id,
    )
    tx = receipt.transaction
    if tx.chama != request.user.chama or (tx.member != request.user and not request.user.is_official):
        messages.error(request, 'Permission denied.')
        return redirect(request.user.get_dashboard_url_name())

    pdf_bytes = build_receipt_pdf_bytes(receipt)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{receipt.receipt_number}.pdf"'
    return response


@role_required(User.Role.TREASURER)
def treasurer_dashboard_view(request):
    chama = request.user.chama
    current_month = '2026-11'

    total_savings = Contribution.objects.filter(chama=chama).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    monthly_contributions = Contribution.objects.filter(chama=chama, month=current_month).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    mpesa_total = PaymentTransaction.objects.filter(
        chama=chama,
        status=PaymentTransaction.Status.SUCCESSFUL,
        payment_method__in=[PaymentTransaction.PaymentMethod.MPESA_STK, PaymentTransaction.PaymentMethod.MPESA_PAYBILL, PaymentTransaction.PaymentMethod.USSD],
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    bank_total = PaymentTransaction.objects.filter(
        chama=chama,
        status=PaymentTransaction.Status.SUCCESSFUL,
        payment_method__in=[PaymentTransaction.PaymentMethod.BANK_TRANSFER, PaymentTransaction.PaymentMethod.BANK_DEPOSIT],
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    pending_verifications = PaymentTransaction.objects.filter(
        chama=chama,
        status=PaymentTransaction.Status.PENDING_VERIFICATION,
    ).select_related('member')

    active_loans = Loan.objects.filter(chama=chama).exclude(status=Loan.Status.REJECTED).select_related('member')
    total_loans_issued = active_loans.aggregate(t=Sum('principal_amount'))['t'] or Decimal('0.00')
    total_outstanding_loans = sum((l.outstanding_balance for l in active_loans if l.status in (Loan.Status.DISBURSED, Loan.Status.APPROVED)), Decimal('0.00'))

    active_members = chama.members.filter(approval_status=User.ApprovalStatus.ACTIVE).order_by('full_name')
    member_rows = []
    overdue_members = []
    for m in active_members:
        acc, _ = SavingsAccount.objects.get_or_create(
            member=m,
            defaults={'chama': chama, 'monthly_target': chama.monthly_contribution},
        )
        paid_nov = acc.has_paid_month(current_month)
        row = {
            'member': m,
            'account': acc,
            'paid_nov': paid_nov,
            'total_savings': acc.total_savings,
        }
        member_rows.append(row)
        if not paid_nov and m.role == User.Role.MEMBER:
            overdue_members.append(row)

    recent_transactions = PaymentTransaction.objects.filter(chama=chama).select_related('member', 'receipt')[:15]
    notifications = TreasurerNotification.objects.filter(chama=chama).select_related('transaction', 'transaction__member')[:12]

    return render(request, 'payments/treasurer_dashboard.html', {
        'chama': chama,
        'total_savings': total_savings,
        'monthly_contributions': monthly_contributions,
        'mpesa_total': mpesa_total,
        'bank_total': bank_total,
        'total_loans_issued': total_loans_issued,
        'total_outstanding_loans': total_outstanding_loans,
        'pending_verifications': pending_verifications,
        'member_rows': member_rows,
        'overdue_members': overdue_members,
        'active_loans': active_loans,
        'recent_transactions': recent_transactions,
        'notifications': notifications,
    })


@role_required(User.Role.TREASURER)
def verify_payment_view(request, tx_id):
    if request.method != 'POST':
        return redirect('payments:treasurer_dashboard')

    tx = get_object_or_404(PaymentTransaction, pk=tx_id, chama=request.user.chama)
    action = request.POST.get('decision')
    if tx.status != PaymentTransaction.Status.PENDING_VERIFICATION:
        messages.warning(request, f'Transaction {tx.external_reference} has already been processed.')
        return redirect('payments:treasurer_dashboard')

    if action == 'verify':
        finalize_verified_payment(tx.pk, verifier=request.user, notes='Verified by Treasurer')
        messages.success(
            request,
            f'Confirmed {tx.get_payment_method_display()} {tx.external_reference} (KES {tx.amount:,.2f}). Member account & receipt updated.',
        )
    elif action == 'reject':
        with transaction.atomic():
            tx.status = PaymentTransaction.Status.REJECTED
            tx.verified_by = request.user
            tx.verified_at = timezone.now()
            tx.save()
            PaymentVerification.objects.create(
                transaction=tx,
                verified_by=request.user,
                decision=PaymentVerification.Decision.REJECTED,
                notes='Declined by Treasurer during reconciliation.',
            )
            notify_treasurer_of_transaction(tx, 'Rejected by Treasurer')
        messages.warning(request, f'Transaction {tx.external_reference} marked Rejected.')

    return redirect('payments:treasurer_dashboard')


@role_required(User.Role.TREASURER)
def mark_notifications_read_view(request):
    if request.method == 'POST':
        TreasurerNotification.objects.filter(chama=request.user.chama, is_read=False).update(is_read=True)
        messages.success(request, 'All payment notifications marked as read.')
    return redirect('payments:treasurer_dashboard')


@role_required(User.Role.TREASURER)
def export_ledger_csv_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="chama-financial-ledger.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Member', 'Member No', 'Month', 'Type', 'Method', 'Reference', 'Status', 'Amount (KES)'])
    txs = PaymentTransaction.objects.filter(chama=request.user.chama).select_related('member')
    for t in txs:
        writer.writerow([
            t.created_at.strftime('%Y-%m-%d %H:%M'),
            t.member.full_name,
            t.member.member_number or '',
            t.contribution_month_label,
            t.get_payment_type_display(),
            t.get_payment_method_display(),
            t.external_reference,
            t.get_status_display(),
            f'{t.amount:.2f}',
        ])
    return response


def ussd_info_view(request):
    """Presents the USSD (*384*240#) offline access mockup and telecom gateway specification."""
    return render(request, 'payments/ussd_access.html', {
        'ussd_code': settings.USSD_SHORTCODE,
    })


@csrf_exempt
def ussd_callback_stub(request):
    """
    Future integration point for Africa's Talking / telecom USSD Gateway webhook.
    Returns standard `CON` / `END` text menus when wired to a live aggregator.
    """
    text = (request.POST.get('text') or request.GET.get('text') or '').strip()
    if text == '':
        body = (
            'CON CHAMA DIGITAL\n'
            '1. My Savings\n'
            '2. Loan Balance\n'
            '3. Make Contribution\n'
            '4. Payment Status\n'
            '5. Meeting Information\n'
            '6. Exit'
        )
    elif text == '6':
        body = 'END Thank you for using Chama Digital.'
    else:
        body = 'END USSD Gateway endpoint ready. Connect telecom aggregator and member PIN verification in production.'
    return HttpResponse(body, content_type='text/plain')
