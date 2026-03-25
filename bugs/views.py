# from django.shortcuts import render
# from django.views.generic import ListView, CreateView, UpdateView, DeleteView
# from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
# from .models import Bug
# from .forms import BugForm
# from django.urls import reverse_lazy
# from django.views.decorators.cache import never_cache
# from django.utils.decorators import method_decorator
# from django.contrib.auth.views import LogoutView



# # @method_decorator(never_cache, name='dispatch')#prevent back button navigation after logout
# class UserBugListView(LoginRequiredMixin, ListView):
#     model = Bug
#     template_name = 'bugs/user_bug_list.html'
#     context_object_name = 'bugs'

#     def get_queryset(self):
#         return Bug.objects.filter(assigned_to = self.request.user)

    
# # @method_decorator(never_cache, name='dispatch')
# class BugCreateView(LoginRequiredMixin, CreateView):
#     model = Bug
#     form_class = BugForm 
#     template_name ='bugs/bug_form.html'
#     success_url = reverse_lazy('bug-list')

#     def form_valid(self,form):
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)


# # @method_decorator(never_cache, name='dispatch')
# class BugUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
#     model = Bug
#     form_class = BugForm
#     template_name = 'bugs/bug_form.html'
#     success_url = reverse_lazy('bug-list')

#     def test_func(self):
#         bug = self.get_object()
#         return bug.created_by == self.request.user

# # @method_decorator(never_cache, name='dispatch')
# class BugDeleteView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
#     model = Bug
#     template_name = 'bugs/bug_confirm_delete.html'
#     success_url = reverse_lazy('bug-list')

#     def test_func(self):
#         bug = self.get_object()
#         return bug.created_by == self.request.user


# # @method_decorator(never_cache, name='dispatch')
# class AllBugListView(LoginRequiredMixin, ListView):
#     model = Bug
#     template_name = 'bugs/all_bug_list.html'
#     context_object_name = 'bugs'

#     def get_queryset(self):
#         return Bug.objects.all()     


# @method_decorator(never_cache, name='dispatch')
# class UserLogoutView(LogoutView):
    # next_page = 'login' 




from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from django.http import HttpResponse

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from django.core.mail import send_mail
from django.conf import settings

import pandas as pd

from .models import Bug
from .forms import BugForm, ProfileForm

import random
import string

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout, authenticate
from django.contrib.auth.mixins import PermissionRequiredMixin



class UserBugListView(ListView):
    model = Bug
    template_name = 'bugs/user_bug_list.html'
    context_object_name = 'bugs'

    def get_queryset(self):

        user = self.request.user

        # Admin sees all bugs
        if user.is_superuser:
            return Bug.objects.all()

        
        return Bug.objects.filter(created_by=user)


class BugCreateView(CreateView):           
    model = Bug
    form_class = BugForm
    template_name = 'bugs/bug_form.html'
    success_url = reverse_lazy('bug-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class BugUpdateView(PermissionRequiredMixin, UpdateView):
    model = Bug
    form_class = BugForm
    template_name = 'bugs/bug_form.html'
    success_url = reverse_lazy('bug_list')

    permission_required = 'bugs.change_bug'

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        print("User:", request.user)
        print("Has perm:", request.user.has_perm('bugs.change_bug'))
        print("Groups:", request.user.groups.all())
        return super().dispatch(request, *args, **kwargs)


class BugDeleteView(UserPassesTestMixin, DeleteView): 
    model = Bug
    template_name = 'bugs/bug_confirm_delete.html'
    success_url = reverse_lazy('bug-list')

    def test_func(self):
        bug = self.get_object()
        return bug.created_by == self.request.user


class AllBugListView(ListView):            
    model = Bug
    template_name = 'bugs/all_bug_list.html'
    context_object_name = 'bugs'

    def get_queryset(self):
        return Bug.objects.all()


class UserLogoutView(LogoutView):
    next_page = 'login'


class BugDownloadView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = request.user

        # Filter data
        if user.is_superuser:
            bugs = Bug.objects.all()
        else:
            bugs = Bug.objects.filter(created_by=user)

        # Convert to list of dicts
        data = []
        for bug in bugs:
            data.append({
                "Bug ID": bug.bug_id,
                "Title": bug.title,
                "Description": bug.description,
                "Status": bug.status,
                "Priority": bug.priority,
                "Progress": bug.progress,
                "Time Spent": bug.time_spent,
                "Assigned To": bug.assigned_to.username if bug.assigned_to else "",
                "Created At": bug.created_at.replace(tzinfo=None) if bug.created_at else "",})
        #  Create DataFrame
        df = pd.DataFrame(data)

        #  Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=bugs.xlsx'

        #  Write Excel
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Bugs')

        return response


class BugUploadView(LoginRequiredMixin, View):

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            messages.error(request, "No file uploaded")
            return redirect('bug-list')

        if not file.name.endswith('.xlsx'):
            messages.error(request, "Only .xlsx files allowed")
            return redirect('bug-list')

        try:
            df = pd.read_excel(file)

            required_columns = ['Bug ID', 'Title', 'Description', 'Status', 'Priority']
            if not all(col in df.columns for col in required_columns):
                messages.error(request, "Invalid Excel format. Required columns missing.")
                return redirect('bug-list')

            created_count = 0
            updated_count = 0
            error_rows = []

            for index, row in df.iterrows():

                bug_id = str(row['Bug ID']).strip()

                if not bug_id:
                    continue

                existing_bug = Bug.objects.filter(bug_id=bug_id).first()

                #  If exists and belongs to another user → ERROR
                if existing_bug and existing_bug.created_by != request.user:
                    error_rows.append(f"Row {index + 2}: Bug ID {bug_id} already exists for another user")
                    continue

                #  Update if same user
                if existing_bug:
                    existing_bug.title = str(row['Title'])
                    existing_bug.description = str(row['Description'])
                    existing_bug.status = row['Status']
                    existing_bug.priority = row['Priority']
                    existing_bug.save()
                    updated_count += 1

                #  Create new
                else:
                    Bug.objects.create(
                        bug_id=bug_id,
                        title=str(row['Title']),
                        description=str(row['Description']),
                        status=row['Status'],
                        priority=row['Priority'],
                        created_by=request.user
                    )
                    created_count += 1

            #  Show messages
            if error_rows:
                messages.error(request, "Some rows failed:\n" + "\n".join(error_rows[:5]))

            messages.success(
                request,
                f"{created_count} created, {updated_count} updated"
            )

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('bug-list')


def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'bugs/profile.html', {'profile_user': user})


@login_required
def profile_edit(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)

        if form.is_valid():
            form.save()

            # Update user safely
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name  = form.cleaned_data.get('last_name', user.last_name)
            user.email      = form.cleaned_data.get('email', user.email)

            user.save()

            messages.success(request, 'Profile updated successfully.')
            return redirect('profile', username=user.username)
        else:
            print(form.errors)  # DEBUG

    else:
        form = ProfileForm(instance=profile)

    return render(request, 'bugs/profile_edit.html', {'form': form})


def generate_temp_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def custom_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No account found with that email.')
            return render(request, 'bugs/password_reset.html')

        #  Generate temporary password
        temp_password = generate_temp_password()

        #  Set new password securely
        user.set_password(temp_password)
        user.save()

        # Send email
        try:
            send_mail(
                subject='🐞 Bug Tracker - Temporary Password',
                message=(
                    f"Hello {user.username},\n\n"
                    f"Your temporary password is:\n\n"
                    f"{temp_password}\n\n"
                    f"Please login and change your password immediately.\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return redirect('password_reset_done')

        except Exception as e:
            messages.error(request, f'Email sending failed: {e}')
            return render(request, 'bugs/password_reset.html')

    return render(request, 'bugs/password_reset.html')




class AdminCreateUserView(UserPassesTestMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'bugs/create_user.html'
    success_url = reverse_lazy('bug-list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        print("FORM VALID - creating user") #todo
        return super().form_valid(form)

    def form_invalid(self, form):
        print(" FORM INVALID - errors:", form.errors)  # ← shows exact error in terminal
        return super().form_invalid(form)
        





@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Check old password using authenticate instead of check_password
        if not authenticate(username=user.username, password=old_password):
            messages.error(request, "Old password is incorrect")
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('change_password')

        user.set_password(new_password)
        user.save()

        logout(request)

        messages.success(request, "Password updated successfully")
        return redirect('login')

    return render(request, 'bugs/change_password.html')



