from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.student_register, name='student-register'),
    path('admin-signup/', views.admin_signup, name='admin-signup'),
    path('dashboard/', views.dashboard_redirect, name='dashboard-redirect'),
]
