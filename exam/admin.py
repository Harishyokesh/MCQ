from django.contrib import admin

from .models import Exam, Question, StudentAnswer, TestAttempt, ViolationLog


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_active', 'duration_minutes', 'max_violations', 'created_at')
    list_filter = ('is_active',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'text', 'correct_option', 'marks', 'order')
    list_filter = ('exam',)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'status', 'score', 'violation_count', 'start_time', 'end_time')
    list_filter = ('status', 'exam')


admin.site.register(StudentAnswer)
admin.site.register(ViolationLog)
