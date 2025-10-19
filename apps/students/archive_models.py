"""
Archive Management System for Student Records
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Student

User = get_user_model()

class StudentArchive(models.Model):
    """Archive system for old/alumni students"""
    ARCHIVE_REASONS = [
        ('graduated', 'Graduated'),
        ('transferred', 'Transferred'),
        ('dropped', 'Dropped Out'),
        ('inactive', 'Inactive'),
        ('alumni', 'Alumni'),
    ]
    
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='archive_record')
    archive_reason = models.CharField(max_length=20, choices=ARCHIVE_REASONS)
    archive_date = models.DateTimeField(auto_now_add=True)
    archived_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='archived_students')
    notes = models.TextField(blank=True, help_text="Additional notes about the archive")
    
    # Archive metadata
    original_grade = models.CharField(max_length=50, blank=True)
    original_section = models.CharField(max_length=50, blank=True)
    graduation_year = models.CharField(max_length=10, blank=True)
    transfer_school = models.CharField(max_length=200, blank=True)
    
    # Data preservation
    archived_data = models.JSONField(default=dict, help_text="Snapshot of student data at time of archiving")
    
    class Meta:
        ordering = ['-archive_date']
    
    def __str__(self):
        return f"Archived: {self.student.user.get_full_name()} ({self.get_archive_reason_display()})"
    
    @property
    def is_graduated(self):
        return self.archive_reason == 'graduated'
    
    @property
    def is_transferred(self):
        return self.archive_reason == 'transferred'
    
    @property
    def is_alumni(self):
        return self.archive_reason in ['graduated', 'alumni']

class ArchivePolicy(models.Model):
    """Archive policies and rules"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Auto-archive rules
    auto_archive_after_years = models.IntegerField(default=5, help_text="Auto-archive students inactive for X years")
    auto_archive_graduated = models.BooleanField(default=True, help_text="Auto-archive graduated students")
    auto_archive_transferred = models.BooleanField(default=True, help_text="Auto-archive transferred students")
    
    # Retention policies
    keep_graduated_records_years = models.IntegerField(default=10, help_text="Keep graduated student records for X years")
    keep_transferred_records_years = models.IntegerField(default=7, help_text="Keep transferred student records for X years")
    
    # Data cleanup
    cleanup_old_archives = models.BooleanField(default=True, help_text="Clean up very old archive records")
    cleanup_after_years = models.IntegerField(default=15, help_text="Clean up archives older than X years")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class ArchiveLog(models.Model):
    """Log of archive operations"""
    ACTION_CHOICES = [
        ('archived', 'Student Archived'),
        ('restored', 'Student Restored'),
        ('auto_archived', 'Auto-Archived'),
        ('bulk_archived', 'Bulk Archived'),
        ('cleanup', 'Archive Cleanup'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    affected_count = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class ArchiveManager:
    """Manager class for archive operations"""
    
    @staticmethod
    def archive_student(student, reason, archived_by, notes=''):
        """Archive a student"""
        # Create archive record
        archive = StudentArchive.objects.create(
            student=student,
            archive_reason=reason,
            archived_by=archived_by,
            notes=notes,
            original_grade=student.grade.name if student.grade else '',
            original_section=student.section.name if student.section else '',
            archived_data=ArchiveManager._get_student_snapshot(student)
        )
        
        # Update student status
        student.is_active = False
        student.save()
        
        # Log the action
        ArchiveLog.objects.create(
            action='archived',
            student=student,
            performed_by=archived_by,
            details=f"Student archived: {reason}"
        )
        
        return archive
    
    @staticmethod
    def restore_student(student_id, restored_by):
        """Restore a student from archive"""
        try:
            archive = StudentArchive.objects.get(student__student_id=student_id)
            student = archive.student
            
            # Restore student status
            student.is_active = True
            student.save()
            
            # Log the action
            ArchiveLog.objects.create(
                action='restored',
                student=student,
                performed_by=restored_by,
                details=f"Student restored from archive"
            )
            
            # Delete archive record
            archive.delete()
            
            return True
        except StudentArchive.DoesNotExist:
            return False
    
    @staticmethod
    def auto_archive_inactive_students():
        """Auto-archive students based on policy"""
        policy = ArchivePolicy.objects.filter(is_active=True).first()
        if not policy:
            return 0
        
        cutoff_date = timezone.now() - timedelta(days=policy.auto_archive_after_years * 365)
        
        # Find inactive students
        inactive_students = Student.objects.filter(
            is_active=True,
            last_login__lt=cutoff_date
        )
        
        archived_count = 0
        for student in inactive_students:
            ArchiveManager.archive_student(
                student=student,
                reason='inactive',
                archived_by=User.objects.filter(is_superuser=True).first(),
                notes=f'Auto-archived after {policy.auto_archive_after_years} years of inactivity'
            )
            archived_count += 1
        
        if archived_count > 0:
            ArchiveLog.objects.create(
                action='auto_archived',
                performed_by=User.objects.filter(is_superuser=True).first(),
                details=f'Auto-archived {archived_count} inactive students',
                affected_count=archived_count
            )
        
        return archived_count
    
    @staticmethod
    def cleanup_old_archives():
        """Clean up very old archive records"""
        policy = ArchivePolicy.objects.filter(is_active=True).first()
        if not policy or not policy.cleanup_old_archives:
            return 0
        
        cutoff_date = timezone.now() - timedelta(days=policy.cleanup_after_years * 365)
        
        # Find old archives
        old_archives = StudentArchive.objects.filter(archive_date__lt=cutoff_date)
        count = old_archives.count()
        
        # Delete old archives
        old_archives.delete()
        
        if count > 0:
            ArchiveLog.objects.create(
                action='cleanup',
                performed_by=User.objects.filter(is_superuser=True).first(),
                details=f'Cleaned up {count} old archive records',
                affected_count=count
            )
        
        return count
    
    @staticmethod
    def _get_student_snapshot(student):
        """Get a snapshot of student data for archiving"""
        return {
            'student_id': student.student_id,
            'name': student.user.get_full_name(),
            'email': student.user.email,
            'lrn': student.lrn,
            'grade': student.grade.name if student.grade else None,
            'section': student.section.name if student.section else None,
            'contact_number': student.contact_number,
            'address': student.address,
            'birth_date': student.birth_date.isoformat() if student.birth_date else None,
            'enrollment_date': student.enrollment_date.isoformat() if student.enrollment_date else None,
            'is_active': student.is_active,
            'created_at': student.created_at.isoformat(),
            'updated_at': student.updated_at.isoformat(),
        }
    
    @staticmethod
    def get_archive_statistics():
        """Get archive statistics"""
        total_archived = StudentArchive.objects.count()
        graduated = StudentArchive.objects.filter(archive_reason='graduated').count()
        transferred = StudentArchive.objects.filter(archive_reason='transferred').count()
        dropped = StudentArchive.objects.filter(archive_reason='dropped').count()
        inactive = StudentArchive.objects.filter(archive_reason='inactive').count()
        
        return {
            'total_archived': total_archived,
            'graduated': graduated,
            'transferred': transferred,
            'dropped': dropped,
            'inactive': inactive,
        }
