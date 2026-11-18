from django.contrib import admin
from .models import Contribution, SavingsAccount


@admin.register(SavingsAccount)
class SavingsAccountAdmin(admin.ModelAdmin):
    list_display = ('member', 'chama', 'monthly_target', 'total_savings')
    list_filter = ('chama',)


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('member', 'month_label', 'amount', 'status', 'created_at')
    list_filter = ('status', 'month', 'chama')
