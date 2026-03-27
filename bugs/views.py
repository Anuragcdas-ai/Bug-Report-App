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




# Django generic views
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View

# Django shortcuts and HTTP
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse

# URL utilities
from django.urls import reverse_lazy

# Auth and permissions
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.views import LogoutView
from django.contrib.auth import update_session_auth_hash, logout, authenticate
from django.contrib.auth.tokens import default_token_generator

# Messages
from django.contrib import messages

# Utilities
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

# Third-party
import pandas as pd
import random
import string

# Django ORM
from django.db.models import Count, Q

# Local app
from .models import Bug, Profile
from .forms import BugForm, ProfileForm, AdminUserCreationForm
from .serializers import DeveloperBugStatsSerializer

# Django REST Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Avg
from .models import Sprint, Bug 
from .forms import SprintForm, BugForm





class UserBugListView(ListView):
    model = Bug
    template_name = 'bugs/user_bug_list.html'
    context_object_name = 'bugs'
    paginate_by = 10  # Add pagination for better performance

    def get_queryset(self):
        user = self.request.user
        
        # Base queryset
        if user.is_superuser:
            queryset = Bug.objects.all()
        else:
            queryset = Bug.objects.filter(created_by=user)
        
        # Apply sprint filter
        sprint_id = self.request.GET.get('sprint')
        if sprint_id:
            queryset = queryset.filter(sprint_id=sprint_id)
        
        # Apply platform filter - FIX for CharField
        platform_value = self.request.GET.get('platform')
        if platform_value:
            # Since platforms is a CharField, filter by exact match or contains
            queryset = queryset.filter(platforms__icontains=platform_value)
        
        # Apply status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')  # Show newest first

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all active sprints for filter dropdown
        from .models import Sprint
        context['sprints'] = Sprint.objects.filter(is_active=True).order_by('-created_at')
        
        # Get unique platform values from existing bugs for filter dropdown
        # This ensures only platforms that actually have bugs are shown
        context['platforms'] = Bug.objects.values_list('platforms', flat=True).distinct().order_by('platforms')
        
        return context


# Update BugCreateView to handle sprints
class BugCreateView(CreateView):
    model = Bug
    form_class = BugForm
    template_name = 'bugs/bug_form.html'
    success_url = reverse_lazy('bug-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['sprint'].required = True
        form.fields['platforms'].required = False

        if not self.request.user.has_perm('bugs.can_change_status'):
            form.fields['status'].required = False

        return form

    def form_valid(self, form):
        if not self.request.user.has_perm('bugs.can_change_status'):
            form.instance.status = 'Open'

        self.object = form.save(commit=False)
        self.object.created_by = self.request.user

        if not form.cleaned_data.get('sprint'):
            messages.error(self.request, 'Bug must be assigned to a sprint!')
            return self.form_invalid(form)

        self.object.save()

        form.save_m2m()   # 🔥 CRITICAL FIX

        messages.success(self.request, 'Bug created successfully!')
        return redirect(self.success_url)

   


# Update BugUpdateView similarly
class BugUpdateView(UpdateView):
    model = Bug
    form_class = BugForm
    template_name = 'bugs/bug_form.html'
    success_url = reverse_lazy('bug-list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        
        # Make sprint required
        form.fields['sprint'].required = True
        form.fields['platforms'].required = False
        
        if user.has_perm('bugs.can_change_status') and not user.has_perm('bugs.change_bug'):
            form.fields = {
                key: value for key, value in form.fields.items()
                if key == 'status'
            }
        
        return form
    
    def form_valid(self, form):
        user = self.request.user
        bug = self.get_object()
        
        # Backend protection
        if user.has_perm('bugs.can_change_status') and not user.has_perm('bugs.change_bug'):
            for field in [f.name for f in Bug._meta.fields]:
                if field != 'status' and field != 'id':
                    setattr(form.instance, field, getattr(bug, field))
        
        form.instance.updated_by = user
        messages.success(self.request, 'Bug updated successfully!')
        return super().form_valid(form)


class BugDeleteView(UserPassesTestMixin, DeleteView): 
    model = Bug
    template_name = 'bugs/bug_confirm_delete.html'
    success_url = reverse_lazy('bug-list')

    def test_func(self):
        bug = self.get_object()
        user = self.request.user
        return user.is_superuser or bug.created_by == user


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

    can_edit = False
    if request.user.is_authenticated:
        can_edit = request.user.is_superuser or (
            request.user == user and
            request.user.has_perm('bugs.edit_user_profile_perm')
        )

    return render(request, 'bugs/profile.html', {
        'profile_user': user,
        'can_edit': can_edit
    })


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
    form_class = AdminUserCreationForm
    template_name = 'bugs/create_user.html'
    success_url = reverse_lazy('bug-list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        # Save the User first
        response = super().form_valid(form)

        # self.object is the newly created User
        user = self.object
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        user.save()

        # Update the Profile (auto-created by signal)
        profile = user.profile
        profile.role = form.cleaned_data['role']
        profile.save()  # triggers assign_user_to_group signal

        return response

    def form_invalid(self, form):
        print("FORM INVALID - errors:", form.errors)
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



class DeveloperBugStatsAPIView(APIView):

    def get(self, request):
        developers = User.objects.filter(profile__role='developer')

        data = []

        for user in developers:
            stats = Bug.objects.filter(assigned_to=user).aggregate(
                completed=Count('id', filter=Q(status='Closed')),
                in_progress=Count('id', filter=Q(status='In Progress')),
                pending=Count('id', filter=Q(status='Open')),
            )

            data.append({
                "username": user.username,
                "full_name": user.get_full_name() or user.username,
                "email": user.email,
                "role": user.profile.role,

                "completed": stats['completed'],
                "in_progress": stats['in_progress'],
                "pending": stats['pending'],
            })

        serializer = DeveloperBugStatsSerializer(data, many=True)
        return Response(serializer.data)
    


class SprintListView(LoginRequiredMixin, ListView):
    model = Sprint
    template_name = 'sprints/sprint_list.html'
    context_object_name = 'sprints'
    paginate_by = 20
    success_url = reverse_lazy('bug-list')
    
    def get_queryset(self):
        return Sprint.objects.all().order_by('-created_at')


class SprintCreateView(LoginRequiredMixin, CreateView):
    model = Sprint
    form_class = SprintForm
    template_name = 'sprints/sprint_form.html'
    success_url = reverse_lazy('sprint-list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Sprint created successfully!')
        return super().form_valid(form)


class SprintUpdateView(LoginRequiredMixin, UpdateView):
    model = Sprint
    form_class = SprintForm
    template_name = 'sprints/sprint_form.html'
    success_url = reverse_lazy('sprint-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Sprint updated successfully!')
        return super().form_valid(form)


class SprintDetailView(LoginRequiredMixin, DetailView):
    model = Sprint
    template_name = 'sprints/sprint_detail.html'
    context_object_name = 'sprint'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sprint = self.get_object()
        
        # Get all bugs in this sprint
        context['bugs'] = sprint.bugs.all().order_by('-created_at')
        
        # Get platform-wise average time spent
        context['platform_avg_time'] = sprint.platform_wise_avg_time()
        
        # Get developer-wise average time spent
        context['developer_avg_time'] = sprint.developer_wise_avg_time()
        
        # Get total hours spent per developer
        context['developer_hours'] = sprint.developer_hours_spent()
        
        # Total time spent in sprint
        context['total_hours'] = sprint.total_hours_spent()
        
        return context


class SprintDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Sprint
    template_name = 'sprints/sprint_confirm_delete.html'
    success_url = reverse_lazy('sprint-list')
    
    def test_func(self):
        sprint = self.get_object()
        return self.request.user.is_superuser or sprint.created_by == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Sprint deleted successfully!')
        return super().delete(request, *args, **kwargs)
    


# Add user-wise average time spent on bugs
class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate average time spent per bug for each user
        users_with_avg = []
        for user in context['users']:
            bug_stats = Bug.objects.filter(assigned_to=user).aggregate(
                total_time=Sum('time_spent'),
                bug_count=Count('id', filter=Q(assigned_to=user))
            )
            
            avg_time = 0
            if bug_stats['bug_count'] > 0:
                avg_time = bug_stats['total_time'] / bug_stats['bug_count'] / 60  # Convert to hours
            
            users_with_avg.append({
                'user': user,
                'avg_time_spent': avg_time,
                'total_bugs': bug_stats['bug_count'],
                'total_time': bug_stats['total_time'] / 60 if bug_stats['total_time'] else 0
            })
        
        context['users_with_avg'] = users_with_avg
        return context



