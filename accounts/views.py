from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render


def home_redirect(request):
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard-redirect')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard-redirect')
        messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.is_staff:
        return redirect('admin-dashboard')
    return redirect('student-dashboard')


def student_register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif password != confirm:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, 'Account created successfully. Good luck!')
            return redirect('student-dashboard')

    return render(request, 'accounts/register.html')


def admin_signup(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm', '')

        if code != settings.ADMIN_SIGNUP_CODE:
            messages.error(request, 'Invalid admin signup code.')
        elif not username or not password:
            messages.error(request, 'Username and password are required.')
        elif password != confirm:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'That username is already taken.')
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password, is_staff=True
            )
            login(request, user)
            messages.success(request, 'Admin account created successfully.')
            return redirect('admin-dashboard')

    return render(request, 'accounts/admin_signup.html')
