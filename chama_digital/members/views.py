from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import MembershipApprovalLog, User
from accounts.permissions import active_chama_member_required, role_required
from announcements.models import Announcement
from loans.models import Loan, LoanApplication
from loans.services import calculate_loan_eligibility
from meetings.models import ChamaEvent
from payments.models import PaymentTransaction
from savings.models import Contribution, SavingsAccount
from .forms import ChamaPasswordChangeForm, MemberProfileEditForm


@role_required(User.Role.CHAIRPERSON)
def chairperson_dashboard_view(request):
    chama = request.user.chama
    all_members = chama.members.filter(role=User.Role.MEMBER)
    pending_apps = all_members.filter(approval_status=User.ApprovalStatus.PENDING).order_by('-created_at')
    approved_members = all_members.filter(approval_status=User.ApprovalStatus.ACTIVE).order_by('full_name')
    rejected_apps = all_members.filter(approval_status=User.ApprovalStatus.REJECTED).order_by('-updated_at')

    total_active_people = chama.members.filter(approval_status=User.ApprovalStatus.ACTIVE).count()
    total_group_savings = Contribution.objects.filter(chama=chama).aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    loans = Loan.objects.filter(chama=chama).select_related('member')
    outstanding_loans = sum(
        (l.outstanding_balance for l in loans if l.status in (Loan.Status.APPROVED, Loan.Status.DISBURSED)),
        Decimal('0.00'),
    )
    loan_applications = list(LoanApplication.objects.filter(chama=chama).select_related('member')[:8])
    for la in loan_applications:
        la.eligibility_info = calculate_loan_eligibility(la.member)
    recent_transactions = PaymentTransaction.objects.filter(chama=chama).select_related('member')[:8]
    upcoming_meetings = ChamaEvent.objects.filter(
        chama=chama,
        is_cancelled=False,
        event_date__gte=timezone.localdate(),
    )[:4]
    recent_announcements = Announcement.objects.filter(chama=chama)[:4]

    return render(request, 'members/chairperson_dashboard.html', {
        'chama': chama,
        'total_members': all_members.count(),
        'active_members_count': total_active_people,
        'pending_apps': pending_apps,
        'approved_members': approved_members,
        'rejected_apps': rejected_apps,
        'total_group_savings': total_group_savings,
        'outstanding_loans': outstanding_loans,
        'loan_applications': loan_applications,
        'loans': loans[:8],
        'recent_transactions': recent_transactions,
        'upcoming_meetings': upcoming_meetings,
        'recent_announcements': recent_announcements,
    })


@role_required(User.Role.CHAIRPERSON)
def review_member_application_view(request, member_id):
    if request.method != 'POST':
        return redirect('members:chairperson_dashboard')

    applicant = get_object_or_404(
        User,
        pk=member_id,
        chama=request.user.chama,
        role=User.Role.MEMBER,
    )
    decision = request.POST.get('decision')
    notes = (request.POST.get('notes') or '').strip()

    with transaction.atomic():
        if decision == 'approve':
            applicant.approve(request.user)
            SavingsAccount.objects.get_or_create(
                member=applicant,
                defaults={'chama': request.user.chama, 'monthly_target': request.user.chama.monthly_contribution},
            )
            MembershipApprovalLog.objects.create(
                member=applicant,
                reviewed_by=request.user,
                decision=User.ApprovalStatus.ACTIVE,
                notes=notes or 'Approved by Chairperson.',
            )
            messages.success(
                request,
                f'Approved {applicant.full_name} ({applicant.member_number}). Full member dashboard access is now unlocked.',
            )
        elif decision == 'reject':
            applicant.approval_status = User.ApprovalStatus.REJECTED
            applicant.approved_by = request.user
            applicant.approved_at = timezone.now()
            applicant.save()
            MembershipApprovalLog.objects.create(
                member=applicant,
                reviewed_by=request.user,
                decision=User.ApprovalStatus.REJECTED,
                notes=notes or 'Declined by Chairperson.',
            )
            messages.warning(
                request,
                f'Declined application for {applicant.full_name}. Dashboard access remains blocked.',
            )

    return redirect('members:chairperson_dashboard')


@active_chama_member_required
def member_directory_view(request):
    """
    Lists approved members of the SAME chama only.
    Intentionally excludes savings balances, contributions, and loan records.
    """
    query = (request.GET.get('q') or '').strip()
    peers = User.objects.filter(
        chama=request.user.chama,
        approval_status=User.ApprovalStatus.ACTIVE,
    ).order_by('full_name')

    if query:
        peers = peers.filter(
            Q(full_name__icontains=query)
            | Q(member_number__icontains=query)
            | Q(role__icontains=query)
        )

    return render(request, 'members/directory.html', {
        'chama': request.user.chama,
        'peers': peers,
        'query': query,
    })


@active_chama_member_required
def member_public_profile_view(request, member_id):
    """Public peer profile within the same chama — strictly no savings or loan balances."""
    peer = get_object_or_404(
        User,
        pk=member_id,
        chama=request.user.chama,
        approval_status=User.ApprovalStatus.ACTIVE,
    )
    return render(request, 'members/public_profile.html', {'peer': peer})


@active_chama_member_required
def my_profile_view(request):
    profile_form = MemberProfileEditForm(instance=request.user)
    password_form = ChamaPasswordChangeForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('form_action')
        if action == 'edit_profile':
            profile_form = MemberProfileEditForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile details have been updated.')
                return redirect('members:my_profile')
        elif action == 'change_password':
            password_form = ChamaPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password has been updated securely.')
                return redirect('members:my_profile')

    savings_total = Decimal('0.00')
    loan_balance = Decimal('0.00')
    if request.user.role == User.Role.MEMBER:
        acc, _ = SavingsAccount.objects.get_or_create(
            member=request.user,
            defaults={'chama': request.user.chama, 'monthly_target': request.user.chama.monthly_contribution},
        )
        savings_total = acc.total_savings
        active_loans = Loan.objects.filter(
            member=request.user,
            chama=request.user.chama,
            status__in=[Loan.Status.APPROVED, Loan.Status.DISBURSED],
        )
        loan_balance = sum((l.outstanding_balance for l in active_loans), Decimal('0.00'))

    return render(request, 'members/my_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'savings_total': savings_total,
        'loan_balance': loan_balance,
    })
