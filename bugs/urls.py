from django.urls import path
from .views import UserBugListView,BugCreateView,BugUpdateView,BugDeleteView,AllBugListView
urlpatterns = [
    path('',UserBugListView.as_view(), name = 'bug-list'),
    path('add/',BugCreateView.as_view(),name = 'bug-add'),
    path('edit/<int:pk>',BugUpdateView.as_view(), name ='bug-edit'),
    path('delete/<int:pk>',BugDeleteView.as_view(), name = 'bug-delete'),
    path('all-bugs/', AllBugListView.as_view(), name='all-bugs'),
    
    
    
]

