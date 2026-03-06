

from django import forms
from .models import Bug

from django import forms
from .models import Bug

class BugForm(forms.ModelForm):

    class Meta:
        model = Bug
        fields = [
            'title',
            'description',
            'status',
            'priority',
            'progress',
            'time_spent',
            'assigned_to',
            'due_date',
            'notes',
            'image'
        ]
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long")
        return title

    def clean_description(self):
        description = self.cleaned_data.get("description")
        if len(description) < 10:
            raise forms.ValidationError("Description must be at least 10 characters")
        return description
