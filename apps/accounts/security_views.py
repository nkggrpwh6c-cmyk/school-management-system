"""
Security views for monitoring and managing security features
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from .models import LoginAttempt, SecurityEvent, TwoFactorAuth, PasswordHistory
from django.contrib.auth import get_user_model

User = get_user_model()


def is_admin_or_security_staff(user):
    """Check if user is admin or has security permissions"""
    return user.is_superuser or user.is_staff or user.role == 'ADMIN'


@login_required
@user_passes_test(is_admin_or_security_staff)
def security_dashboard(request):
    """Security dashboard for administrators"""
    
    # Time ranges for analysis
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Login attempts analysis
    recent_attempts = LoginAttempt.objects.filter(timestamp__gte=last_24h)
    failed_attempts = recent_attempts.filter(success=False)
    successful_attempts = recent_attempts.filter(success=True)
    
    # Security events analysis
    security_events = SecurityEvent.objects.filter(timestamp__gte=last_24h)
    suspicious_events = security_events.filter(event_type='SUSPICIOUS_ACTIVITY')
    
    # Top failed login IPs
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
    
    # Get additional data for comprehensive dashboard
    recent_failed_logins = failed_attempts.order_by('-timestamp')[:10]
    recent_security_events = security_events.order_by('-timestamp')[:10]
    user_activity = SecurityEvent.objects.filter(
        timestamp__gte=last_24h,
        event_type__in=['ADMIN_ACTION', 'USER_ACTION']
    ).order_by('-timestamp')[:10]
    system_changes = SecurityEvent.objects.filter(
        timestamp__gte=last_7d,
        event_type='ADMIN_ACTION'
    ).order_by('-timestamp')[:15]
    
    # Active users (logged in within last hour)
    active_users = User.objects.filter(
        last_login__gte=now - timedelta(hours=1)
    ).count()
    
    # Locked accounts (estimate based on recent failed attempts)
    locked_accounts = failed_attempts.values('username').annotate(
        count=Count('username')
    ).filter(count__gte=5).count()
    
    context = {
        'failed_login_count': failed_attempts.count(),
        'successful_login_count': successful_attempts.count(),
        'security_events_count': security_events.count(),
        'active_users': active_users,
        'locked_accounts': locked_accounts,
        'two_fa_enabled': users_with_2fa,
        'recent_failed_logins': recent_failed_logins,
        'recent_security_events': recent_security_events,
        'user_activity': user_activity,
        'system_changes': system_changes,
    }
    
    return render(request, 'accounts/security_dashboard_modern.html', context)


@login_required
@user_passes_test(is_admin_or_security_staff)
def security_events(request):
    """View all security events"""
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
    from django.core.paginator import Paginator
    paginator = Paginator(events, 50)
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)
    
    context = {
        'events': events,
        'event_types': SecurityEvent.EVENT_TYPES,
    }
    
    return render(request, 'accounts/security_events.html', context)


@login_required
@user_passes_test(is_admin_or_security_staff)
def login_attempts(request):
    """View all login attempts"""
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
    from django.core.paginator import Paginator
    paginator = Paginator(attempts, 50)
    page_number = request.GET.get('page')
    attempts = paginator.get_page(page_number)
    
    context = {
        'attempts': attempts,
    }
    
    return render(request, 'accounts/login_attempts.html', context)


@login_required
def security_settings(request):
    """User security settings page"""
    user = request.user
    
    # Get or create 2FA settings
    two_fa, created = TwoFactorAuth.objects.get_or_create(user=user)
    
    # Generate QR code URL if 2FA is not enabled
    qr_code_url = None
    if not two_fa.is_enabled and not two_fa.secret_key:
        two_fa.generate_secret_key()
        qr_code_url = two_fa.get_qr_code_url()
    
    context = {
        'two_fa': two_fa,
        'qr_code_url': qr_code_url,
    }
    
    return render(request, 'accounts/security_settings.html', context)


@login_required
def enable_2fa(request):
    """Enable 2FA for user"""
    if request.method == 'POST':
        user = request.user
        two_fa, created = TwoFactorAuth.objects.get_or_create(user=user)
        
        # Generate secret key and backup codes
        two_fa.generate_secret_key()
        backup_codes = two_fa.generate_backup_codes()
        
        messages.success(request, '2FA setup initiated. Please scan the QR code with your authenticator app.')
        
        return redirect('accounts:security_settings')
    
    return redirect('accounts:security_settings')


@login_required
def verify_2fa_setup(request):
    """Verify 2FA setup with TOTP token"""
    if request.method == 'POST':
        token = request.POST.get('token')
        user = request.user
        
        try:
            two_fa = TwoFactorAuth.objects.get(user=user)
            if two_fa.verify_totp(token):
                two_fa.is_enabled = True
                two_fa.save()
                messages.success(request, '2FA has been successfully enabled!')
            else:
                messages.error(request, 'Invalid token. Please try again.')
        except TwoFactorAuth.DoesNotExist:
            messages.error(request, '2FA setup not found.')
        
        return redirect('accounts:security_settings')
    
    return redirect('accounts:security_settings')


@login_required
def disable_2fa(request):
    """Disable 2FA for user"""
    if request.method == 'POST':
        user = request.user
        
        try:
            two_fa = TwoFactorAuth.objects.get(user=user)
            two_fa.is_enabled = False
            two_fa.secret_key = ''
            two_fa.backup_codes = []
            two_fa.save()
            messages.success(request, '2FA has been disabled.')
        except TwoFactorAuth.DoesNotExist:
            messages.error(request, '2FA not found.')
        
        return redirect('accounts:security_settings')
    
    return redirect('accounts:security_settings')


@login_required
@user_passes_test(is_admin_or_security_staff)
def security_analytics(request):
    """Security analytics and reports"""
    
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
    
    return render(request, 'accounts/security_analytics.html', context)
