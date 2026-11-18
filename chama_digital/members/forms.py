from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from accounts.models import User


class MemberProfileEditForm(forms.ModelForm):
    """Allows a member to update only safe personal profile fields."""

    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'bio', 'profile_photo', 'show_phone_in_directory']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control mono-figure'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short personal bio or business focus...'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'show_phone_in_directory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'show_phone_in_directory': 'Display my phone number to fellow members in the Chama Directory',
        }


class ChamaPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
