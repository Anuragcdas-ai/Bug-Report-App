from django.urls import path
from django.contrib.auth import views as auth_views
from .views import UserBugListView,BugCreateView,BugUpdateView,BugDeleteView,AllBugListView,BugDownloadView, BugUploadView,profile_view,profile_edit,custom_password_reset,AdminCreateUserView

urlpatterns = [
    path('',UserBugListView.as_view(), name = 'bug-list'),
    path('add/',BugCreateView.as_view(),name = 'bug-add'),
    path('edit/<int:pk>',BugUpdateView.as_view(), name ='bug-edit'),
    path('delete/<int:pk>',BugDeleteView.as_view(), name = 'bug-delete'),
    path('all-bugs/', AllBugListView.as_view(), name='all-bugs'),
    path('download/', BugDownloadView.as_view(), name='bug-download'),
    path('upload/', BugUploadView.as_view(), name='bug-upload'),
    
    path('profile/edit/', profile_edit, name='profile-settings'),

        # User Management (Superuser only)
    path('users/create/', AdminCreateUserView.as_view(), name='create-user'),

    # Dynamic route LAST
    path('profile/<str:username>/', profile_view, name='profile'),
    path('password_reset/', custom_password_reset, name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='bugs/password_reset_done.html'
         ),
         name='password_reset_done'),

   
    
    
]

