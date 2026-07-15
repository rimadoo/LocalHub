from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'location', 'budget', 'category']  # Correct properties mapping
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'e.g. Fixing Water Tap'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-4', 'rows': 4, 'placeholder': 'Describe the work details...'}),
            'location': forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'e.g. Uttara Sector 4'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control rounded-pill', 'placeholder': '0.00'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-pill'}),
        }