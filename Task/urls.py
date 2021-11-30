from django.urls import path
from Task import views
from Task import admin

urlpatterns = [
    path('developer', views.getDevelopers),
    path('record', views.getTaskRecord),
    path('check', views.checkTask),
    path('revoke', views.revokeTask),
    path('addtask', views.addTask),
    path('submit', views.submitTask),
    path('pull', views.getRequest),
    path('delete', views.deleteTask)
]
