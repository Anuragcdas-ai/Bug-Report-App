

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Bug, Profile

from django import forms
from .models import Bug, Sprint




class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = '__all__'
        widgets = {
            'developers': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        lead = cleaned_data.get('lead_developer')
        developers = cleaned_data.get('developers')

        if lead and developers and lead in developers:
            raise forms.ValidationError(
                "Lead developer cannot be in developers list"
            )

        return cleaned_data

class BugForm(forms.ModelForm):

    class Meta:
        model = Bug
        fields = ['title', 'description', 'status', 'priority', 'progress', 
                  'assigned_to', 'due_date', 'notes', 'sprint', 'platforms']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active sprints
        self.fields['sprint'].queryset = Sprint.objects.filter(is_active=True)
        self.fields['assigned_to'].queryset = User.objects.filter(profile__role='developer')
        
        # Add platform choices
        self.fields['platforms'].widget = forms.CheckboxSelectMultiple()   

   

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