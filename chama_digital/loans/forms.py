from decimal import Decimal
from django import forms


class LoanApplicationForm(forms.Form):
    requested_amount = forms.DecimalField(
        label='Requested Loan Amount (KES)',
        min_value=Decimal('1000.00'),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control mono-figure', 'placeholder': 'e.g. 25000', 'step': '500'}),
    )
    repayment_months = forms.ChoiceField(
        label='Repayment Period',
        choices=[(3, '3 Months'), (6, '6 Months'), (12, '12 Months')],
        initial=6,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    purpose = forms.CharField(
        label='Loan Purpose',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Business stock expansion or school fees'}),
    )

    def __init__(self, *args, max_eligible_amount=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_eligible_amount = max_eligible_amount
        if max_eligible_amount is not None and max_eligible_amount >= Decimal('1000.00'):
            self.fields['requested_amount'].widget.attrs['max'] = str(max_eligible_amount)

    def clean_requested_amount(self):
        amount = self.cleaned_data['requested_amount']
        if self.max_eligible_amount is not None:
            if self.max_eligible_amount < Decimal('1000.00'):
                raise forms.ValidationError(
                    'You are not currently eligible to apply for a new loan based on your verified savings and active commitments.'
                )
            if amount > self.max_eligible_amount:
                raise forms.ValidationError(
                    f'Requested amount exceeds your eligible savings-based limit of KES {self.max_eligible_amount:,.2f}.'
                )
        return amount


class OfficialRepaymentForm(forms.Form):
    amount = forms.DecimalField(
        label='Repayment Amount (KES)',
        min_value=Decimal('100.00'),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control mono-figure', 'step': '100'}),
    )
    reference = forms.CharField(
        label='Payment Reference',
        max_length=80,
        widget=forms.TextInput(attrs={'class': 'form-control mono-figure', 'placeholder': 'e.g. SK991204 or KCB-REP-11'}),
    )
