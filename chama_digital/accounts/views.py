import uuid
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from savings.models import SavingsAccount
from .forms import (
    ChamaLoginForm,
    ContactInquiryForm,
    MemberRegistrationForm,
    OfficialRegistrationForm,
)
from .models import ChamaGroup, User


def home_view(request):
    """Public Chama Digital homepage preserving original design + server-side contact form."""
    if request.method == 'POST':
        contact_form = ContactInquiryForm(request.POST)
        if contact_form.is_valid():
            contact_form.save()
            messages.success(
                request,
                'Thank you! Your inquiry has been received and saved. Our Chama Digital onboarding team will reach out shortly.',
            )
            return redirect('/#contact')
        messages.error(request, 'Please correct the errors in the contact form below.')
    else:
        contact_form = ContactInquiryForm()

    sample_chama = ChamaGroup.objects.first()
    return render(request, 'home.html', {
        'contact_form': contact_form,
        'sample_chama': sample_chama,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url_name())

    form = ChamaLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['identifier']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me', False)

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            messages.error(request, 'Invalid email/phone number or password.')
        elif user.approval_status == User.ApprovalStatus.REJECTED:
            messages.error(
                request,
                'Your membership application was rejected by the Chairperson and cannot access the dashboard.',
            )
        else:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            if user.approval_status == User.ApprovalStatus.PENDING:
                return redirect('accounts:pending_approval')
            messages.success(request, f'Welcome back, {user.full_name}.')
            return redirect(user.get_dashboard_url_name())

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out securely.')
        return redirect('accounts:login')
    return redirect(request.user.get_dashboard_url_name())


def register_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url_name())

    active_tab = request.GET.get('tab', 'member')
    member_form = MemberRegistrationForm()
    official_form = OfficialRegistrationForm()

    if request.method == 'POST':
        reg_type = request.POST.get('registration_type', 'member')
        if reg_type == 'official':
            active_tab = 'official'
            official_form = OfficialRegistrationForm(request.POST)
            if official_form.is_valid():
                with transaction.atomic():
                    chama_name = official_form.cleaned_data['chama_name'].strip()
                    chama = ChamaGroup.objects.filter(name__iexact=chama_name).first()
                    if not chama:
                        invite_slug = f'CHM-{uuid.uuid4().hex[:4].upper()}'
                        chama = ChamaGroup.objects.create(
                            name=chama_name,
                            invite_code=invite_slug,
                        )
                    email = official_form.cleaned_data['email']
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=official_form.cleaned_data['password'],
                        full_name=official_form.cleaned_data['full_name'].strip(),
                        phone_number=official_form.cleaned_data['phone_number'].strip(),
                        chama=chama,
                        role=official_form.cleaned_data['role'],
                        approval_status=User.ApprovalStatus.ACTIVE,
                        approved_at=timezone.now(),
                    )
                    user.assign_next_member_number()
                    user.save()
                    SavingsAccount.objects.get_or_create(
                        member=user,
                        defaults={'chama': chama, 'monthly_target': chama.monthly_contribution},
                    )
                login(request, user, backend='accounts.backends.EmailOrPhoneBackend')
                messages.success(
                    request,
                    f'Official account created for {user.get_role_display()} ({chama.name}).',
                )
                return redirect(user.get_dashboard_url_name())
        else:
            active_tab = 'member'
            member_form = MemberRegistrationForm(request.POST, request.FILES)
            if member_form.is_valid():
                with transaction.atomic():
                    chama = member_form.cleaned_chama
                    email = member_form.cleaned_data['email']
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=member_form.cleaned_data['password'],
                        full_name=member_form.cleaned_data['full_name'].strip(),
                        phone_number=member_form.cleaned_data['phone_number'].strip(),
                        national_id=member_form.cleaned_data['national_id'].strip(),
                        profile_photo=member_form.cleaned_data.get('profile_photo'),
                        chama=chama,
                        role=User.Role.MEMBER,
                        approval_status=User.ApprovalStatus.PENDING,
                    )
                    SavingsAccount.objects.get_or_create(
                        member=user,
                        defaults={'chama': chama, 'monthly_target': chama.monthly_contribution},
                    )
                login(request, user, backend='accounts.backends.EmailOrPhoneBackend')
                messages.success(
                    request,
                    'Your registration has been received successfully. Your membership is awaiting chairperson approval.',
                )
                return redirect('accounts:pending_approval')

    return render(request, 'accounts/register.html', {
        'member_form': member_form,
        'official_form': official_form,
        'active_tab': active_tab,
    })


@login_required
def pending_approval_view(request):
    if request.user.approval_status == User.ApprovalStatus.ACTIVE:
        return redirect(request.user.get_dashboard_url_name())
    return render(request, 'accounts/pending_approval.html', {'applicant': request.user})


@login_required
def dashboard_redirect_view(request):
    return redirect(request.user.get_dashboard_url_name())
