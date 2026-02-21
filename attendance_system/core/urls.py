# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.teacher_dashboard, name='dashboard'),
    path('generate-qr/', views.generate_qr, name='generate_qr'),
    path('export/', views.export_attendance, name='export_attendance'),
    path('student/mark/<uuid:token>/', views.mark_attendance, name='mark_attendance'),
    path('attendance-success/', views.attendance_success, name='attendance_success'),
    path('attendance-expired/', views.attendance_expired, name='attendance_expired'),
    path('ajax/get-subjects/', views.get_subjects_by_class_year, name='get_subjects'),
]
