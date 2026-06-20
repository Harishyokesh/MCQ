from django.contrib.auth.models import User
from django.db import models


class Exam(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    max_violations = models.PositiveIntegerField(
        default=3, help_text='Number of tab-switch warnings allowed before auto-submit.'
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_exams')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def total_marks(self):
        return sum(q.marks for q in self.questions.all())

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    OPTION_CHOICES = [('A', 'Option A'), ('B', 'Option B'), ('C', 'Option C'), ('D', 'Option D')]

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.exam.title} - Q{self.order}'


class TestAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('auto_submitted', 'Auto Submitted (Violations)'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.FloatField(default=0)
    violation_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f'{self.student.username} - {self.exam.title}'


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        unique_together = ('attempt', 'question')


class ViolationLog(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='violations')
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=100, default='tab_switch')
