from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from accounts.permissions import role_required
from .forms import LoanApplicationForm, OfficialRepaymentForm
from .models import Loan, LoanApplication, LoanRepayment
from .services import calculate_loan_eligibility


@role_required(User.Role.MEMBER)
def member_loans_view(request):
    chama = request.user.chama
    eligibility = calculate_loan_eligibility(request.user)
    form = LoanApplicationForm(
        request.POST or None,
        max_eligible_amount=eligibility['remaining_apply_capacity'],
    )

    if request.method == 'POST' and form.is_valid():
        LoanApplication.objects.create(
            member=request.user,
            chama=chama,
            requested_amount=form.cleaned_data['requested_amount'],
            repayment_months=int(form.cleaned_data['repayment_months']),
            purpose=form.cleaned_data['purpose'].strip(),
        )
        messages.success(
            request,
            'Loan application submitted! It is now visible to the Chairperson and Treasurer for review.',
        )
        return redirect('loans:member_loans')

    applications = LoanApplication.objects.filter(member=request.user, chama=chama)
    loans = Loan.objects.filter(member=request.user, chama=chama).prefetch_related('repayments')
    repayments = LoanRepayment.objects.filter(loan__member=request.user, loan__chama=chama).select_related('loan')

    active_loans = [l for l in loans if l.status in (Loan.Status.APPROVED, Loan.Status.DISBURSED)]
    outstanding_balance = sum((l.outstanding_balance for l in active_loans), Decimal('0.00'))
    total_repaid = sum((l.total_repaid for l in loans), Decimal('0.00'))
    next_due = active_loans[0].next_repayment_date if active_loans else None

    return render(request, 'loans/member_loans.html', {
        'form': form,
        'eligibility': eligibility,
        'applications': applications,
        'loans': loans,
        'repayments': repayments,
        'outstanding_balance': outstanding_balance,
        'total_repaid': total_repaid,
        'next_due': next_due,
    })


@role_required(User.Role.CHAIRPERSON, User.Role.TREASURER)
def review_loan_application_view(request, app_id):
    if request.method != 'POST':
        return redirect(request.user.get_dashboard_url_name())

    app = get_object_or_404(LoanApplication, pk=app_id, chama=request.user.chama)
    decision = request.POST.get('decision')
    if app.status != LoanApplication.Status.PENDING:
        messages.warning(request, 'This loan application has already been reviewed.')
        return redirect(request.user.get_dashboard_url_name())

    with transaction.atomic():
        if decision == 'approve':
            app.status = LoanApplication.Status.APPROVED
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
            app.save()

            loan_count = Loan.objects.filter(chama=request.user.chama).count()
            Loan.objects.create(
                application=app,
                loan_code=f'LN-{timezone.now().year}-{loan_count + 1:03d}',
                member=app.member,
                chama=app.chama,
                principal_amount=app.requested_amount,
                repayment_months=app.repayment_months,
                purpose=app.purpose,
                next_repayment_date=timezone.localdate() + timedelta(days=30),
                status=Loan.Status.DISBURSED,
                disbursed_by=request.user,
                disbursed_at=timezone.now(),
            )
            messages.success(
                request,
                f'Loan application for {app.member.full_name} (KES {app.requested_amount:,.2f}) approved and activated.',
            )
        elif decision == 'reject':
            app.status = LoanApplication.Status.REJECTED
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
            app.save()
            messages.warning(request, f'Loan application for {app.member.full_name} rejected.')

    return redirect(request.user.get_dashboard_url_name())


@role_required(User.Role.CHAIRPERSON, User.Role.TREASURER)
def record_loan_repayment_view(request, loan_id):
    if request.method != 'POST':
        return redirect(request.user.get_dashboard_url_name())

    loan = get_object_or_404(Loan, pk=loan_id, chama=request.user.chama)
    form = OfficialRepaymentForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            amount = form.cleaned_data['amount']
            LoanRepayment.objects.create(
                loan=loan,
                amount=amount,
                reference=form.cleaned_data['reference'].strip().upper(),
                recorded_by=request.user,
            )
            if loan.outstanding_balance <= Decimal('0.00'):
                loan.status = Loan.Status.COMPLETED
                loan.save()
        messages.success(request, f'Recorded repayment of KES {amount:,.2f} on {loan.loan_code}.')
    else:
        messages.error(request, 'Invalid repayment details provided.')
    return redirect(request.user.get_dashboard_url_name())
