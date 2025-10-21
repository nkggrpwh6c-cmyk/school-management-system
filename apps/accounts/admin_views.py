"""
Admin Dashboard Views
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import User, LoginAttempt, SecurityEvent, TwoFactorAuth
from apps.students.models import Student
from apps.students.archive_models import StudentArchive
from apps.documents.sf10_models import SF10Document


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    """Modern admin dashboard with comprehensive statistics"""
    
    # Time ranges
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=now - timedelta(hours=1)).count()
    
    # Student statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    
    # Security statistics
    failed_logins = LoginAttempt.objects.filter(
        timestamp__gte=last_24h,
        success=False
    ).count()
    security_events = SecurityEvent.objects.filter(timestamp__gte=last_24h).count()
    
    # SF10 statistics
    total_sf10 = SF10Document.objects.count()
    complete_sf10 = SF10Document.objects.filter(is_complete=True).count()
    
    # Archive statistics
    archived_students = StudentArchive.objects.count()
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_students': total_students,
        'active_students': active_students,
        'failed_logins': failed_logins,
        'security_events': security_events,
        'total_sf10': total_sf10,
        'complete_sf10': complete_sf10,
        'archived_students': archived_students,
    }
    
    return render(request, 'admin/modern_dashboard.html', context)
