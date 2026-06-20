from django.urls import path

from . import views

urlpatterns = [
    # Admin
    path('admin/', views.admin_dashboard, name='admin-dashboard'),
    path('admin/create/', views.create_exam, name='create-exam'),
    path('admin/<int:exam_id>/upload/', views.upload_questions, name='upload-questions'),
    path('admin/template/', views.download_template, name='download-template'),
    path('admin/question/<int:question_id>/delete/', views.delete_question, name='delete-question'),
    path('admin/<int:exam_id>/toggle/', views.toggle_exam_active, name='toggle-exam-active'),
    path('admin/<int:exam_id>/results/', views.exam_results, name='exam-results'),

    # Student
    path('dashboard/', views.student_dashboard, name='student-dashboard'),
    path('start/<int:exam_id>/', views.start_exam, name='start-exam'),
    path('take/<int:attempt_id>/', views.take_exam, name='take-exam'),
    path('take/<int:attempt_id>/violation/', views.log_violation, name='log-violation'),
    path('result/<int:attempt_id>/', views.view_result, name='view-result'),
]
