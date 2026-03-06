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


class UserBugListView(ListView):           # ✅ no LoginRequiredMixin
    model = Bug
    template_name = 'bugs/user_bug_list.html'
    context_object_name = 'bugs'

    def get_queryset(self):
        return Bug.objects.filter(assigned_to=self.request.user)


class BugCreateView(CreateView):           # ✅ no LoginRequiredMixin
    model = Bug
    form_class = BugForm
    template_name = 'bugs/bug_form.html'
    success_url = reverse_lazy('bug-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class BugUpdateView(UserPassesTestMixin, UpdateView):   # ✅ no LoginRequiredMixin
    model = Bug
    form_class = BugForm
    template_name = 'bugs/bug_form.html'
    success_url = reverse_lazy('bug-list')

    def test_func(self):
        bug = self.get_object()
        return bug.created_by == self.request.user


class BugDeleteView(UserPassesTestMixin, DeleteView):   # ✅ no LoginRequiredMixin
    model = Bug
    template_name = 'bugs/bug_confirm_delete.html'
    success_url = reverse_lazy('bug-list')

    def test_func(self):
        bug = self.get_object()
        return bug.created_by == self.request.user


class AllBugListView(ListView):            # ✅ no LoginRequiredMixin
    model = Bug
    template_name = 'bugs/all_bug_list.html'
    context_object_name = 'bugs'

    def get_queryset(self):
        return Bug.objects.all()


class UserLogoutView(LogoutView):
    next_page = 'login'

        




