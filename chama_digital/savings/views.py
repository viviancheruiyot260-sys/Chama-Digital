from decimal import Decimal
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from accounts.permissions import role_required
from announcements.models import Announcement
from loans.models import Loan
from loans.services import calculate_loan_eligibility
from meetings.models import ChamaEvent
from payments.models import PaymentTransaction
from .models import Contribution, SavingsAccount


@role_required(User.Role.MEMBER)
def member_dashboard_view(request):
    chama = request.user.chama
    account, _ = SavingsAccount.objects.get_or_create(
        member=request.user,
        defaults={'chama': chama, 'monthly_target': chama.monthly_contribution},
    )
    current_month = '2026-11'
    total_savings = account.total_savings
    total_contributions = account.total_contributions_count
    nov_paid = account.has_paid_month(current_month)
    nov_total = account.month_total(current_month)

    my_loans = Loan.objects.filter(member=request.user, chama=chama)
    total_borrowed = my_loans.filter(
        status__in=[Loan.Status.APPROVED, Loan.Status.DISBURSED, Loan.Status.COMPLETED]
    ).aggregate(t=Sum('principal_amount'))['t'] or Decimal('0.00')
    active_loans = [l for l in my_loans if l.status in (Loan.Status.DISBURSED, Loan.Status.APPROVED)]
    outstanding_loan_balance = sum((l.outstanding_balance for l in active_loans), Decimal('0.00'))
    total_repaid = sum((l.total_repaid for l in my_loans), Decimal('0.00'))
    loan_eligibility = calculate_loan_eligibility(request.user)

    recent_transactions = PaymentTransaction.objects.filter(
        member=request.user,
        chama=chama,
    ).select_related('receipt')[:6]

    today = timezone.localdate()
    upcoming_events = ChamaEvent.objects.filter(
        chama=chama,
        is_cancelled=False,
        event_date__gte=today,
    ).order_by('event_date', 'event_time')
    next_meeting = upcoming_events.filter(
        event_type__in=[ChamaEvent.EventType.REGULAR_MEETING, ChamaEvent.EventType.AGM]
    ).first() or upcoming_events.first()

    recent_announcements = Announcement.objects.filter(chama=chama)[:5]

    return render(request, 'savings/member_dashboard.html', {
        'chama': chama,
        'account': account,
        'total_savings': total_savings,
        'total_contributions': total_contributions,
        'nov_paid': nov_paid,
        'nov_total': nov_total,
        'outstanding_loan_balance': outstanding_loan_balance,
        'total_borrowed': total_borrowed,
        'total_repaid': total_repaid,
        'loan_eligibility': loan_eligibility,
        'recent_transactions': recent_transactions,
        'next_meeting': next_meeting,
        'upcoming_events': upcoming_events[:5],
        'recent_announcements': recent_announcements,
    })
