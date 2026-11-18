from django.contrib import admin
from .models import Loan, LoanApplication, LoanRepayment


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('member', 'requested_amount', 'repayment_months', 'status', 'created_at')
    list_filter = ('status', 'chama')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_code', 'member', 'principal_amount', 'status', 'next_repayment_date')
    list_filter = ('status', 'chama')


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount', 'reference', 'repaid_at')
