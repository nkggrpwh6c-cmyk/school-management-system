"""
Enhanced Registrar Views with Smart Validation and Modern Features
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
import json

from .models import Student, Grade, Section
from .validators import SmartDataValidator, DuplicateChecker, DataIntegrityChecker
from .archive_models import ArchiveManager, ArchivePolicy
from .backup_system import BackupManager
from apps.documents.sf10_models import SF10Document

def clear_dashboard_cache():
    """Clear dashboard cache when data changes"""
    cache.delete('registrar_dashboard_stats')

def is_admin_or_registrar(user):
    """Check if user is admin or registrar"""
    return user.is_authenticated and (user.is_superuser or user.role == 'ADMIN')

@login_required
def enhanced_registrar_dashboard(request):
    """Enhanced registrar dashboard - ULTRA OPTIMIZED with caching for smooth performance"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    # Check cache first for maximum speed
    cache_key = 'registrar_dashboard_stats'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'students/registrar_dashboard_modern.html', cached_data)
    
    # ULTRA OPTIMIZED: Single query for all statistics
    stats = Student.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(is_active=True)),
        inactive=Count('id', filter=Q(is_active=False))
    )
    
    # Pre-calculate values to avoid template calculations
    total_students = int(stats['total']) if stats['total'] is not None else 0
    active_students = int(stats['active']) if stats['active'] is not None else 0
    inactive_students = int(stats['inactive']) if stats['inactive'] is not None else 0
    
    # Get current year for enrollment stats
    current_year = timezone.now().year
    enrolled_this_year = Student.objects.filter(
        admission_date__year=current_year
    ).count()
    
    # Get document count
    total_documents = SF10Document.objects.count()
    
    # Only load data if there are students (avoid empty queries)
    if total_students > 0:
        # Optimize grade distribution (limit to top 6 for speed)
        grade_distribution = Student.objects.values('grade__name').annotate(
            count=Count('id')
        ).order_by('-count')[:6]
    else:
        # Empty data for fresh system
        grade_distribution = []
    
    # Minimal context for maximum speed
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'graduated_students': inactive_students,  # All inactive = graduated
        'transferred_students': 0,  # No transfers in current model
        'enrolled_this_year': enrolled_this_year,
        'total_documents': total_documents,
        'grade_distribution': grade_distribution,
    }
    
    # Cache for 5 minutes for smooth performance
    cache.set(cache_key, context, 300)
    
    return render(request, 'students/registrar_dashboard_modern.html', context)

@login_required
def smart_student_validation(request):
    """Smart validation endpoint for student data"""
    if not is_admin_or_registrar(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Run comprehensive validation
            validation_result = SmartDataValidator.validate_student_data(data)
            
            # Check for duplicates
            duplicates = DuplicateChecker.check_duplicate_student(data, data.get('student_id'))
            
            return JsonResponse({
                'valid': validation_result['valid'] and len(duplicates) == 0,
                'errors': validation_result['errors'] + duplicates,
                'warnings': validation_result['warnings'],
                'suggestions': get_validation_suggestions(data)
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def archive_student(request, student_id):
    """Archive a student"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('registrar:student_search')
    
    if request.method == 'POST':
        try:
            student = get_object_or_404(Student, student_id=student_id)
            reason = request.POST.get('reason', 'inactive')
            notes = request.POST.get('notes', '')
            
            # Archive the student
            archive = ArchiveManager.archive_student(
                student=student,
                reason=reason,
                archived_by=request.user,
                notes=notes
            )
            
            messages.success(request, f"Student {student.user.get_full_name()} has been archived successfully.")
            return redirect('registrar:student_search')
            
        except Exception as e:
            messages.error(request, f"Failed to archive student: {str(e)}")
            return redirect('registrar:student_detail', student_id=student_id)
    
    return redirect('registrar:student_search')

@login_required
def restore_student(request, student_id):
    """Restore a student from archive"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('registrar:student_search')
    
    try:
        success = ArchiveManager.restore_student(student_id, request.user)
        if success:
            messages.success(request, "Student has been restored successfully.")
        else:
            messages.error(request, "Student not found in archive.")
    except Exception as e:
        messages.error(request, f"Failed to restore student: {str(e)}")
    
    return redirect('registrar:student_search')

@login_required
def bulk_archive_students(request):
    """Bulk archive students"""
    if not is_admin_or_registrar(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_ids = data.get('student_ids', [])
            reason = data.get('reason', 'inactive')
            notes = data.get('notes', '')
            
            archived_count = 0
            for student_id in student_ids:
                try:
                    student = Student.objects.get(student_id=student_id)
                    ArchiveManager.archive_student(
                        student=student,
                        reason=reason,
                        archived_by=request.user,
                        notes=notes
                    )
                    archived_count += 1
                except Student.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'archived_count': archived_count,
                'message': f'Successfully archived {archived_count} students.'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def create_backup(request):
    """Create manual backup"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('registrar:enhanced_dashboard')
    
    try:
        backup_manager = BackupManager()
        backup_name = backup_manager.create_backup('manual')
        
        if backup_name:
            messages.success(request, f"Backup created successfully: {backup_name}")
        else:
            messages.error(request, "Failed to create backup.")
    except Exception as e:
        messages.error(request, f"Backup failed: {str(e)}")
    
    return redirect('registrar:enhanced_dashboard')

@login_required
def system_health_check(request):
    """System health check endpoint"""
    if not is_admin_or_registrar(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    health_status = {
        'data_integrity': check_data_integrity(),
        'backup_status': check_backup_status(),
        'validation_errors': get_validation_errors(),
        'archive_status': get_archive_status(),
        'system_performance': get_system_performance(),
    }
    
    return JsonResponse(health_status)

@login_required
def auto_archive_inactive(request):
    """Run auto-archive for inactive students"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('registrar:enhanced_dashboard')
    
    try:
        archived_count = ArchiveManager.auto_archive_inactive_students()
        messages.success(request, f"Auto-archived {archived_count} inactive students.")
    except Exception as e:
        messages.error(request, f"Auto-archive failed: {str(e)}")
    
    return redirect('registrar:enhanced_dashboard')

@login_required
def cleanup_old_archives(request):
    """Clean up old archive records"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('registrar:enhanced_dashboard')
    
    try:
        cleaned_count = ArchiveManager.cleanup_old_archives()
        messages.success(request, f"Cleaned up {cleaned_count} old archive records.")
    except Exception as e:
        messages.error(request, f"Cleanup failed: {str(e)}")
    
    return redirect('registrar:enhanced_dashboard')

# Helper functions
def check_data_integrity():
    """Check data integrity across the system"""
    issues = []
    
    # Check for students without SF10 records
    students_without_sf10 = Student.objects.filter(sf10_records__isnull=True).count()
    if students_without_sf10 > 0:
        issues.append(f"{students_without_sf10} students without SF10 records")
    
    # Check for SF10 records without students
    sf10_without_students = SF10Document.objects.filter(student__isnull=True).count()
    if sf10_without_students > 0:
        issues.append(f"{sf10_without_students} SF10 records without students")
    
    return {
        'status': 'healthy' if len(issues) == 0 else 'warning',
        'issues': issues
    }

def check_backup_status():
    """Check backup system status"""
    try:
        backup_manager = BackupManager()
        # Check if backup directory exists and is writable
        import os
        backup_dir = backup_manager.backup_dir
        if os.path.exists(backup_dir) and os.access(backup_dir, os.W_OK):
            return {'status': 'healthy', 'message': 'Backup system operational'}
        else:
            return {'status': 'error', 'message': 'Backup directory not accessible'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_validation_errors():
    """Get current validation errors in the system"""
    errors = []
    
    # Check for students with future birth dates
    from datetime import date
    students_with_future_birth = Student.objects.filter(date_of_birth__gt=date.today()).count()
    if students_with_future_birth > 0:
        errors.append(f"{students_with_future_birth} students with future birth dates")
    
    # Check for students with missing parent information
    students_missing_parent_phone = Student.objects.filter(parent_phone__isnull=True).count()
    if students_missing_parent_phone > 0:
        errors.append(f"{students_missing_parent_phone} students missing parent phone")
    
    # Check for students with missing emergency contact
    students_missing_emergency = Student.objects.filter(
        models.Q(emergency_contact__isnull=True) | models.Q(emergency_contact='')
    ).count()
    if students_missing_emergency > 0:
        errors.append(f"{students_missing_emergency} students missing emergency contact")
    
    # Check for students with invalid email formats
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    
    students_with_invalid_email = 0
    for student in Student.objects.filter(parent_email__isnull=False).exclude(parent_email=''):
        try:
            validate_email(student.parent_email)
        except ValidationError:
            students_with_invalid_email += 1
    
    if students_with_invalid_email > 0:
        errors.append(f"{students_with_invalid_email} students with invalid parent email format")
    
    return {
        'count': len(errors),
        'errors': errors
    }

def get_archive_status():
    """Get archive system status"""
    try:
        stats = ArchiveManager.get_archive_statistics()
        return {
            'status': 'healthy',
            'total_archived': stats['total_archived'],
            'graduated': stats['graduated'],
            'transferred': stats['transferred']
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_system_performance():
    """Get system performance metrics"""
    try:
        # Simple performance check
        import time
        start_time = time.time()
        
        # Test database query performance
        Student.objects.count()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        return {
            'status': 'healthy' if query_time < 1.0 else 'warning',
            'query_time': query_time,
            'message': 'Database performance normal' if query_time < 1.0 else 'Database performance slow'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_validation_suggestions(data):
    """Get validation suggestions for student data"""
    suggestions = []
    
    # Suggest guardian contact if guardian name is provided
    if data.get('guardian_name') and not data.get('guardian_contact'):
        suggestions.append("Consider adding guardian contact number")
    
    # Suggest email if contact number is not provided
    if not data.get('contact_number') and not data.get('email'):
        suggestions.append("Consider adding contact information (phone or email)")
    
    # Suggest previous school if transferring
    if data.get('status') == 'transferred' and not data.get('previous_school'):
        suggestions.append("Consider adding previous school information for transferred students")
    
    return suggestions
