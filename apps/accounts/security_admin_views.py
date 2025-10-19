"""
Dedicated security admin views - separate from main admin
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import LoginAttempt, SecurityEvent, TwoFactorAuth, PasswordHistory
from django.contrib.auth import get_user_model

User = get_user_model()


def is_security_admin(user):
    """Check if user is security admin"""
    return (user.is_authenticated and 
            (user.username == 'security_admin' or 
             user.role == 'ADMIN' or 
             user.is_staff))


def security_admin_login(request):
    """Dedicated security admin login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user and is_security_admin(user):
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Accessing security dashboard...')
            return redirect('accounts:security_admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions for security admin access.')
    
    return render(request, 'accounts/security_admin_login.html')


@login_required
@user_passes_test(is_security_admin)
def security_admin_dashboard(request):
    """Dedicated security admin dashboard"""
    
    # Time ranges for analysis
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Security metrics
    recent_attempts = LoginAttempt.objects.filter(timestamp__gte=last_24h)
    failed_attempts = recent_attempts.filter(success=False)
    successful_attempts = recent_attempts.filter(success=True)
    
    security_events = SecurityEvent.objects.filter(timestamp__gte=last_24h)
    suspicious_events = security_events.filter(event_type='SUSPICIOUS_ACTIVITY')
    
    # Top failed IPs
    top_failed_ips = (
        failed_attempts.values('ip_address')
        .annotate(count=Count('ip_address'))
        .order_by('-count')[:10]
    )
    
    # Top failed usernames
    top_failed_users = (
        failed_attempts.values('username')
        .annotate(count=Count('username'))
        .order_by('-count')[:10]
    )
    
    # 2FA statistics
    total_users = User.objects.count()
    users_with_2fa = TwoFactorAuth.objects.filter(is_enabled=True).count()
    two_fa_percentage = (users_with_2fa / total_users * 100) if total_users > 0 else 0
    
    # Recent security events by type
    events_by_type = (
        security_events.values('event_type')
        .annotate(count=Count('event_type'))
        .order_by('-count')
    )
    
    context = {
        'recent_attempts': recent_attempts[:20],
        'failed_attempts_count': failed_attempts.count(),
        'successful_attempts_count': successful_attempts.count(),
        'security_events_count': security_events.count(),
        'suspicious_events_count': suspicious_events.count(),
        'top_failed_ips': top_failed_ips,
        'top_failed_users': top_failed_users,
        'two_fa_percentage': round(two_fa_percentage, 1),
        'users_with_2fa': users_with_2fa,
        'total_users': total_users,
        'events_by_type': events_by_type,
        'last_24h': last_24h,
        'last_7d': last_7d,
        'last_30d': last_30d,
    }
    
    return render(request, 'accounts/security_admin_dashboard.html', context)


@login_required
@user_passes_test(is_security_admin)
def security_login_attempts(request):
    """Security admin view for login attempts"""
    attempts = LoginAttempt.objects.all().order_by('-timestamp')
    
    # Filtering
    success = request.GET.get('success')
    if success is not None:
        attempts = attempts.filter(success=success == 'true')
    
    # Search
    search = request.GET.get('search')
    if search:
        attempts = attempts.filter(
            Q(username__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(attempts, 50)
    page_number = request.GET.get('page')
    attempts = paginator.get_page(page_number)
    
    context = {
        'attempts': attempts,
    }
    
    return render(request, 'accounts/security_login_attempts.html', context)


@login_required
@user_passes_test(is_security_admin)
def security_events_admin(request):
    """Security admin view for security events"""
    events = SecurityEvent.objects.all().order_by('-timestamp')
    
    # Filtering
    event_type = request.GET.get('event_type')
    if event_type:
        events = events.filter(event_type=event_type)
    
    # Search
    search = request.GET.get('search')
    if search:
        events = events.filter(
            Q(description__icontains=search) |
            Q(user__username__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(events, 50)
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)
    
    context = {
        'events': events,
        'event_types': SecurityEvent.EVENT_TYPES,
    }
    
    return render(request, 'accounts/security_events_admin.html', context)


@login_required
@user_passes_test(is_security_admin)
def security_user_management(request):
    """Security admin view for user security management"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filtering
    role = request.GET.get('role')
    if role:
        users = users.filter(role=role)
    
    # Search
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(users, 50)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'role_choices': User.ROLE_CHOICES,
    }
    
    return render(request, 'accounts/security_user_management.html', context)


@login_required
@user_passes_test(is_security_admin)
def security_analytics_admin(request):
    """Security analytics for security admin"""
    
    # Time ranges
    now = timezone.now()
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Login attempts over time
    attempts_7d = LoginAttempt.objects.filter(timestamp__gte=last_7d)
    attempts_30d = LoginAttempt.objects.filter(timestamp__gte=last_30d)
    
    # Security events over time
    events_7d = SecurityEvent.objects.filter(timestamp__gte=last_7d)
    events_30d = SecurityEvent.objects.filter(timestamp__gte=last_30d)
    
    # Failed login trends
    failed_attempts_7d = attempts_7d.filter(success=False).count()
    failed_attempts_30d = attempts_30d.filter(success=False).count()
    
    # Suspicious activity trends
    suspicious_7d = events_7d.filter(event_type='SUSPICIOUS_ACTIVITY').count()
    suspicious_30d = events_30d.filter(event_type='SUSPICIOUS_ACTIVITY').count()
    
    context = {
        'attempts_7d': attempts_7d.count(),
        'attempts_30d': attempts_30d.count(),
        'events_7d': events_7d.count(),
        'events_30d': events_30d.count(),
        'failed_attempts_7d': failed_attempts_7d,
        'failed_attempts_30d': failed_attempts_30d,
        'suspicious_7d': suspicious_7d,
        'suspicious_30d': suspicious_30d,
    }
    
    return render(request, 'accounts/security_analytics_admin.html', context)
