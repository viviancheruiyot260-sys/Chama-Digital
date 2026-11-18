from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import ChamaGroup, ContactInquiry, User


class ChamaLoginForm(forms.Form):
    identifier = forms.CharField(
        label='Email or Phone Number',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'amina@chamadigital.co.ke or +254 712 345 678',
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        }),
    )
    remember_me = forms.BooleanField(
        required=False,
        label='Remember me',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


class MemberRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label='Full Name',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Faith Njeri Kamau'}),
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'faith@example.co.ke'}),
    )
    phone_number = forms.CharField(
        label='Phone Number',
        max_length=25,
        widget=forms.TextInput(attrs={'class': 'form-control mono-figure', 'placeholder': '+254 712 345 678'}),
    )
    national_id = forms.CharField(
        label='National ID Number',
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control mono-figure', 'placeholder': 'e.g. 29481022'}),
    )
    chama_invite_code = forms.CharField(
        label='Chama Invitation Code',
        max_length=30,
        initial='UMJ-2026',
        widget=forms.TextInput(attrs={'class': 'form-control mono-figure', 'placeholder': 'e.g. UMJ-2026'}),
    )
    profile_photo = forms.ImageField(
        label='Profile Photo (Optional)',
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Minimum 8 characters'}),
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter password'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()
        if User.objects.filter(phone_number__iexact=phone).exists():
            raise ValidationError('An account with this phone number already exists.')
        return phone

    def clean_chama_invite_code(self):
        code = self.cleaned_data['chama_invite_code'].strip()
        chama = ChamaGroup.objects.filter(invite_code__iexact=code).first()
        if not chama:
            raise ValidationError('Invalid Chama invitation code. Try UMJ-2026 for Umoja Table Banking Chama.')
        self.cleaned_chama = chama
        return code

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        if password:
            validate_password(password)
        return cleaned


class OfficialRegistrationForm(forms.Form):
    OFFICIAL_ROLE_CHOICES = [
        (User.Role.CHAIRPERSON, 'Chairperson'),
        (User.Role.TREASURER, 'Treasurer'),
        (User.Role.SECRETARY, 'Secretary'),
    ]

    full_name = forms.CharField(
        label='Full Name',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Samuel Kamau'}),
    )
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'official@chamadigital.co.ke'}),
    )
    phone_number = forms.CharField(
        label='Phone Number',
        max_length=25,
        widget=forms.TextInput(attrs={'class': 'form-control mono-figure', 'placeholder': '+254 711 223 344'}),
    )
    chama_name = forms.CharField(
        label='Chama / Group Name',
        max_length=150,
        initial='Umoja Table Banking Chama',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    role = forms.ChoiceField(
        label='Official Position',
        choices=OFFICIAL_ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    official_code = forms.CharField(
        label='Official Onboarding Authorization Code',
        max_length=50,
        help_text='Required security code from the Chama Chairperson or platform administrator.',
        widget=forms.TextInput(attrs={'class': 'form-control mono-figure', 'placeholder': 'Enter authorization code'}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Minimum 8 characters'}),
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter password'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()
        if User.objects.filter(phone_number__iexact=phone).exists():
            raise ValidationError('An account with this phone number already exists.')
        return phone

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        if password:
            validate_password(password)

        chama_name = (cleaned.get('chama_name') or '').strip()
        official_code = (cleaned.get('official_code') or '').strip()
        existing_chama = ChamaGroup.objects.filter(name__iexact=chama_name).first()
        expected_code = (
            existing_chama.official_invite_code
            if existing_chama
            else settings.CHAMA_OFFICIAL_MASTER_CODE
        )
        if official_code != expected_code and official_code != settings.CHAMA_OFFICIAL_MASTER_CODE:
            self.add_error(
                'official_code',
                'Invalid official authorization code. Privileged official accounts require a valid group onboarding code.',
            )
        return cleaned


class ContactInquiryForm(forms.ModelForm):
    class Meta:
        model = ContactInquiry
        fields = ['full_name', 'phone_number', 'chama_name', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Faith Njeri'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254 712 345 678'}),
            'chama_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Umoja Table Banking Chama'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'How can we support your savings group?'}),
        }
