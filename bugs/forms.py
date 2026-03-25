

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Bug, Profile

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



class ProfileForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = ['role']




class AdminUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, required=False)

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'role', 'password1', 'password2'
        ]