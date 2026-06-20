from io import BytesIO

import openpyxl
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ExamForm, UploadExcelForm
from .models import Exam, Question, StudentAnswer, TestAttempt, ViolationLog
from .utils import parse_questions_excel

# ---------------------------------------------------------------------------
# Admin views
# ---------------------------------------------------------------------------


@staff_member_required
def admin_dashboard(request):
    exams = Exam.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'exam/admin_dashboard.html', {'exams': exams})


@staff_member_required
def create_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, 'Exam created. Now upload your questions.')
            return redirect('upload-questions', exam_id=exam.id)
    else:
        form = ExamForm(initial={'is_active': True})
    return render(request, 'exam/create_exam.html', {'form': form})


@staff_member_required
def upload_questions(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)

    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            created, errors = parse_questions_excel(form.cleaned_data['file'], exam)
            if created:
                messages.success(request, f'{created} question(s) imported successfully.')
            for err in errors[:20]:
                messages.warning(request, err)
            if not created and not errors:
                messages.info(request, 'No new questions were found in the file.')
            return redirect('upload-questions', exam_id=exam.id)
    else:
        form = UploadExcelForm()

    questions = exam.questions.all()
    return render(
        request,
        'exam/upload_questions.html',
        {'exam': exam, 'form': form, 'questions': questions},
    )


@staff_member_required
def download_template(request):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = 'Questions'
    sheet.append(
        ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'marks']
    )
    sheet.append(
        ['What is the capital of France?', 'Paris', 'London', 'Berlin', 'Madrid', 'A', 1]
    )
    sheet.append(
        ['Which language is the Django framework written in?', 'Python', 'Java', 'C++', 'Ruby', 'A', 1]
    )
    for col in ('A', 'B', 'C', 'D', 'E', 'F', 'G'):
        sheet.column_dimensions[col].width = 28

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(
        buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="mcq_question_template.xlsx"'
    return response


@staff_member_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, exam__created_by=request.user)
    exam_id = question.exam_id
    question.delete()
    messages.success(request, 'Question deleted.')
    return redirect('upload-questions', exam_id=exam_id)


@staff_member_required
def toggle_exam_active(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    exam.is_active = not exam.is_active
    exam.save(update_fields=['is_active'])
    return redirect('admin-dashboard')


@staff_member_required
def exam_results(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, created_by=request.user)
    attempts = exam.attempts.select_related('student').order_by('-score', 'start_time')
    return render(request, 'exam/exam_results.html', {'exam': exam, 'attempts': attempts})


# ---------------------------------------------------------------------------
# Student views
# ---------------------------------------------------------------------------


@login_required
def student_dashboard(request):
    if request.user.is_staff:
        return redirect('admin-dashboard')

    exams = Exam.objects.filter(is_active=True)
    attempted_ids = set(
        TestAttempt.objects.filter(student=request.user).values_list('exam_id', flat=True)
    )
    my_attempts = (
        TestAttempt.objects.filter(student=request.user).select_related('exam').order_by('-start_time')
    )
    return render(
        request,
        'exam/student_dashboard.html',
        {'exams': exams, 'attempted_ids': attempted_ids, 'my_attempts': my_attempts},
    )


@login_required
def start_exam(request, exam_id):
    if request.user.is_staff:
        return redirect('admin-dashboard')

    exam = get_object_or_404(Exam, id=exam_id, is_active=True)
    attempt, _created = TestAttempt.objects.get_or_create(student=request.user, exam=exam)

    if attempt.status != 'in_progress':
        messages.info(request, 'You have already completed this exam.')
        return redirect('view-result', attempt_id=attempt.id)

    return redirect('take-exam', attempt_id=attempt.id)


@login_required
def take_exam(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, student=request.user)

    if attempt.status != 'in_progress':
        return redirect('view-result', attempt_id=attempt.id)

    exam = attempt.exam
    questions = list(exam.questions.all())

    for q in questions:
        StudentAnswer.objects.get_or_create(attempt=attempt, question=q)
    answers = {a.question_id: a.selected_option for a in attempt.answers.all()}

    if request.method == 'POST':
        for q in questions:
            selected = request.POST.get(f'question_{q.id}') or None
            StudentAnswer.objects.update_or_create(
                attempt=attempt, question=q, defaults={'selected_option': selected}
            )
        _finish_attempt(attempt, auto=request.POST.get('auto_submit') == '1')
        return redirect('view-result', attempt_id=attempt.id)

    elapsed = (timezone.now() - attempt.start_time).total_seconds()
    remaining_seconds = max(0, exam.duration_minutes * 60 - int(elapsed))

    return render(
        request,
        'exam/take_exam.html',
        {
            'attempt': attempt,
            'exam': exam,
            'questions': questions,
            'answers': answers,
            'remaining_seconds': remaining_seconds,
            'max_violations': exam.max_violations,
        },
    )


@login_required
@require_POST
def log_violation(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, student=request.user)

    if attempt.status != 'in_progress':
        return JsonResponse({'status': attempt.status, 'force_submit': False})

    reason = request.POST.get('reason', 'tab_switch')
    ViolationLog.objects.create(attempt=attempt, reason=reason)
    attempt.violation_count += 1
    attempt.save(update_fields=['violation_count'])

    force_submit = attempt.violation_count >= attempt.exam.max_violations
    return JsonResponse(
        {
            'status': 'in_progress',
            'violation_count': attempt.violation_count,
            'max_violations': attempt.exam.max_violations,
            'force_submit': force_submit,
        }
    )


def _finish_attempt(attempt, auto=False):
    score = 0
    for ans in attempt.answers.select_related('question').all():
        if ans.selected_option and ans.selected_option == ans.question.correct_option:
            score += ans.question.marks
    attempt.score = score
    attempt.status = 'auto_submitted' if auto else 'submitted'
    attempt.end_time = timezone.now()
    attempt.save()


@login_required
def view_result(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, student=request.user)
    exam = attempt.exam
    answers = attempt.answers.select_related('question').order_by('question__order')
    return render(
        request, 'exam/result.html', {'attempt': attempt, 'exam': exam, 'answers': answers}
    )
