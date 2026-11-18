from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import ChamaGroup, ContactInquiry, MembershipApprovalLog, User


@admin.register(ChamaGroup)
class ChamaGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'invite_code', 'monthly_contribution', 'next_contribution_date', 'bank_name')
    search_fields = ('name', 'invite_code')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('full_name', 'email', 'phone_number', 'chama', 'role', 'approval_status', 'member_number')
    list_filter = ('role', 'approval_status', 'chama')
    search_fields = ('full_name', 'email', 'phone_number', 'member_number')
    ordering = ('full_name',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Chama Membership', {
            'fields': (
                'full_name', 'phone_number', 'national_id', 'chama', 'role',
                'approval_status', 'member_number', 'profile_photo', 'bio',
                'show_phone_in_directory', 'approved_by', 'approved_at',
            ),
        }),
    )


@admin.register(MembershipApprovalLog)
class MembershipApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('member', 'decision', 'reviewed_by', 'decided_at')
    list_filter = ('decision',)


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'chama_name', 'created_at')
