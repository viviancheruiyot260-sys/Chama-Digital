from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class ChamaGroup(models.Model):
    """Represents a Kenyan table-banking or investment chama group."""

    name = models.CharField(max_length=150, unique=True)
    invite_code = models.CharField(max_length=30, unique=True)
    official_invite_code = models.CharField(
        max_length=50,
        default='UMOJA-OFFICIAL-2026',
        help_text='Required code when registering as Chairperson, Treasurer, or Secretary.',
    )
    monthly_contribution = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('12500.00'),
    )
    next_contribution_date = models.DateField(default='2026-11-30')
    paybill_number = models.CharField(max_length=20, default='522522')
    bank_name = models.CharField(max_length=120, default='Kenya Commercial Bank (KCB)')
    bank_account = models.CharField(max_length=60, default='1184-2093-5510')
    ussd_code = models.CharField(max_length=20, default='*384*240#')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Chama Group'
        verbose_name_plural = 'Chama Groups'

    def __str__(self):
        return f'{self.name} ({self.invite_code})'


class User(AbstractUser):
    """
    Custom Chama Digital user with chama membership, official role,
    and Chairperson approval workflow status.
    """

    class Role(models.TextChoices):
        CHAIRPERSON = 'CHAIRPERSON', 'Chairperson'
        TREASURER = 'TREASURER', 'Treasurer'
        SECRETARY = 'SECRETARY', 'Secretary'
        MEMBER = 'MEMBER', 'Member'

    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        ACTIVE = 'ACTIVE', 'Active'
        REJECTED = 'REJECTED', 'Rejected'

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=25, unique=True)
    national_id = models.CharField(max_length=30, blank=True)
    chama = models.ForeignKey(
        ChamaGroup,
        on_delete=models.PROTECT,
        related_name='members',
        null=True,
        blank=True,
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    member_number = models.CharField(max_length=30, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    default_avatar_path = models.CharField(max_length=120, default='images/avatar-member-amina.jpg')
    bio = models.TextField(blank=True)
    show_phone_in_directory = models.BooleanField(default=True)
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_applications',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.get_role_display()})'

    @property
    def is_approved_member(self):
        return self.approval_status == self.ApprovalStatus.ACTIVE

    @property
    def is_official(self):
        return self.role in (
            self.Role.CHAIRPERSON,
            self.Role.TREASURER,
            self.Role.SECRETARY,
        )

    def get_dashboard_url_name(self):
        if self.approval_status == self.ApprovalStatus.PENDING:
            return 'accounts:pending_approval'
        if self.approval_status == self.ApprovalStatus.REJECTED:
            return 'accounts:login'
        if self.role == self.Role.CHAIRPERSON:
            return 'members:chairperson_dashboard'
        if self.role == self.Role.TREASURER:
            return 'payments:treasurer_dashboard'
        if self.role == self.Role.SECRETARY:
            return 'meetings:secretary_dashboard'
        return 'savings:member_dashboard'

    def assign_next_member_number(self):
        if self.member_number or not self.chama:
            return
        existing_count = User.objects.filter(
            chama=self.chama,
            member_number__isnull=False,
        ).exclude(member_number='').count()
        self.member_number = f'CHM-{existing_count + 1:03d}'

    def approve(self, chairperson_user):
        self.approval_status = self.ApprovalStatus.ACTIVE
        self.approved_by = chairperson_user
        self.approved_at = timezone.now()
        self.assign_next_member_number()
        self.save()


class MembershipApprovalLog(models.Model):
    """Audit trail for Chairperson membership approval and rejection actions."""

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approval_logs',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviewed_applications',
    )
    decision = models.CharField(max_length=20, choices=User.ApprovalStatus.choices)
    notes = models.CharField(max_length=255, blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-decided_at']

    def __str__(self):
        return f'{self.member.full_name} -> {self.decision}'


class ContactInquiry(models.Model):
    """Stores public homepage inquiries from prospective Kenyan chamas."""

    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=30)
    chama_name = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Contact Inquiries'

    def __str__(self):
        return f'{self.full_name} ({self.phone_number})'
