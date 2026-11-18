from decimal import Decimal
from django.db.models import Sum

from savings.models import Contribution
from .models import Loan, LoanApplication

LOAN_SAVINGS_MULTIPLIER = Decimal('3')
MIN_SAVINGS_FOR_LOAN = Decimal('1000.00')
MIN_LOAN_AMOUNT = Decimal('1000.00')


def calculate_loan_eligibility(member) -> dict:
    """
    Computes a member's loan eligibility strictly from verified savings and active/pending loans.

    Rule:
      - Member must be an approved active chama member.
      - Minimum verified savings: KES 1,000.00.
      - Maximum borrowing ceiling: 3x total verified savings.
      - Available borrowing limit: max(0, max_loan_limit - active_loan_balance).
      - Remaining application capacity: max(0, available_loan_limit - pending_applications_total).
    """
    chama = getattr(member, 'chama', None)
    if not chama:
        return {
            'multiplier': int(LOAN_SAVINGS_MULTIPLIER),
            'min_savings_required': MIN_SAVINGS_FOR_LOAN,
            'total_savings': Decimal('0.00'),
            'max_loan_limit': Decimal('0.00'),
            'active_loan_balance': Decimal('0.00'),
            'pending_applications_total': Decimal('0.00'),
            'available_loan_limit': Decimal('0.00'),
            'remaining_apply_capacity': Decimal('0.00'),
            'savings_needed_for_min': MIN_SAVINGS_FOR_LOAN,
            'utilization_percent': 0,
            'is_eligible': False,
            'status_code': 'NOT_APPROVED',
            'status_label': 'Not Eligible',
            'status_css_class': 'status-overdue',
            'reason': 'You must belong to an approved chama group to check loan eligibility.',
        }

    total_savings = (
        Contribution.objects.filter(member=member, chama=chama)
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )
    max_loan_limit = (total_savings * LOAN_SAVINGS_MULTIPLIER).quantize(Decimal('0.01'))

    active_loans = Loan.objects.filter(
        member=member,
        chama=chama,
        status__in=[Loan.Status.APPROVED, Loan.Status.DISBURSED],
    ).prefetch_related('repayments')
    active_loan_balance = sum((l.outstanding_balance for l in active_loans), Decimal('0.00'))

    pending_applications_total = (
        LoanApplication.objects.filter(
            member=member,
            chama=chama,
            status=LoanApplication.Status.PENDING,
        ).aggregate(total=Sum('requested_amount'))['total']
        or Decimal('0.00')
    )

    available_loan_limit = max(Decimal('0.00'), max_loan_limit - active_loan_balance)
    remaining_apply_capacity = max(
        Decimal('0.00'),
        available_loan_limit - pending_applications_total,
    )

    if max_loan_limit > Decimal('0.00'):
        used = min(max_loan_limit, active_loan_balance + pending_applications_total)
        utilization_percent = int(((used / max_loan_limit) * Decimal('100')).quantize(Decimal('1')))
    else:
        utilization_percent = 0

    savings_needed_for_min = max(Decimal('0.00'), MIN_SAVINGS_FOR_LOAN - total_savings)

    if not member.is_approved_member:
        is_eligible = False
        status_code = 'NOT_APPROVED'
        status_label = 'Pending Approval'
        status_css_class = 'status-pending'
        reason = 'Your membership must be approved by the Chairperson before you can apply for loans.'
    elif total_savings < MIN_SAVINGS_FOR_LOAN:
        is_eligible = False
        status_code = 'NOT_YET_ELIGIBLE'
        status_label = 'Not Yet Eligible'
        status_css_class = 'status-overdue'
        reason = (
            f'Build at least KES {MIN_SAVINGS_FOR_LOAN:,.2f} in verified savings '
            f'(need KES {savings_needed_for_min:,.2f} more) to unlock loans up to '
            f'{int(LOAN_SAVINGS_MULTIPLIER)}x your savings.'
        )
    elif available_loan_limit < MIN_LOAN_AMOUNT:
        is_eligible = False
        status_code = 'LIMIT_REACHED'
        status_label = 'Limit Reached'
        status_css_class = 'status-pending'
        reason = (
            f'Your active loan balance (KES {active_loan_balance:,.2f}) has reached your '
            f'{int(LOAN_SAVINGS_MULTIPLIER)}x savings ceiling (KES {max_loan_limit:,.2f}). '
            f'Repay active loans or add verified savings to unlock more credit.'
        )
    elif remaining_apply_capacity < MIN_LOAN_AMOUNT:
        is_eligible = False
        status_code = 'PENDING_CAPACITY'
        status_label = 'Pending Review'
        status_css_class = 'status-pending'
        reason = (
            f'Pending loan applications totaling KES {pending_applications_total:,.2f} '
            f'cover your remaining borrowing limit of KES {available_loan_limit:,.2f}.'
        )
    else:
        is_eligible = True
        status_code = 'ELIGIBLE'
        status_label = 'Eligible for Loan'
        status_css_class = 'status-paid'
        reason = (
            f'You qualify to apply for up to KES {remaining_apply_capacity:,.2f} '
            f'({int(LOAN_SAVINGS_MULTIPLIER)}x your verified savings of KES {total_savings:,.2f}, '
            f'less any active or pending loan commitments).'
        )

    return {
        'multiplier': int(LOAN_SAVINGS_MULTIPLIER),
        'min_savings_required': MIN_SAVINGS_FOR_LOAN,
        'total_savings': total_savings,
        'max_loan_limit': max_loan_limit,
        'active_loan_balance': active_loan_balance,
        'pending_applications_total': pending_applications_total,
        'available_loan_limit': available_loan_limit,
        'remaining_apply_capacity': remaining_apply_capacity,
        'savings_needed_for_min': savings_needed_for_min,
        'utilization_percent': utilization_percent,
        'is_eligible': is_eligible,
        'status_code': status_code,
        'status_label': status_label,
        'status_css_class': status_css_class,
        'reason': reason,
    }
