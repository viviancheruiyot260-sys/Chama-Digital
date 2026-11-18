from django import forms
from .models import ChamaEvent


class ChamaEventForm(forms.ModelForm):
    class Meta:
        model = ChamaEvent
        fields = ['event_type', 'title', 'event_date', 'event_time', 'venue', 'agenda', 'description', 'minutes_summary']
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Monthly Table-Banking Meeting or AGM'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'event_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 10:00 AM EAT'}),
            'venue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Umoja Community Hall, Nairobi'}),
            'agenda': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Key agenda items...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Occasion details or notes...'}),
            'minutes_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional meeting minutes summary'}),
        }
