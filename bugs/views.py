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
from django.contrib.auth.mixins import UserPassesTestMixin
from .models import Bug
from .forms import BugForm
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView
import pandas as pd
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Bug
import pandas as pd
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Bug
import pandas as pd
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Bug


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


class BugUpdateView(UserPassesTestMixin, UpdateView):  
    model = Bug
    form_class = BugForm
    template_name = 'bugs/bug_form.html'
    success_url = reverse_lazy('bug-list')

    def test_func(self):
        bug = self.get_object()
        return bug.created_by == self.request.user


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

            required_columns = ['Title', 'Description', 'Status', 'Priority']
            if not all(col in df.columns for col in required_columns):
                messages.error(request, "Invalid Excel format")
                return redirect('bug-list')

            created_count = 0

            for _, row in df.iterrows():
                Bug.objects.create(
                    title=str(row['Title']),
                    description=str(row['Description']),
                    status=row['Status'],
                    priority=row['Priority'],
                    created_by=request.user
                )
                created_count += 1

            messages.success(request, f"{created_count} bugs uploaded successfully")

        except Exception as e:
            messages.error(request, str(e))

        return redirect('bug-list')

        




