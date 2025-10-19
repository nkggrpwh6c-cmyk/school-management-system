from django.db import models
from django.contrib.auth import get_user_model
from apps.students.models import Student

User = get_user_model()

class SF10Document(models.Model):
    """SF10 (Student Form 10) Document Management"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('transferred', 'Transferred'),
        ('archived', 'Archived'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='sf10_records')
    school_year = models.CharField(max_length=20, help_text='e.g., 2023-2024')
    grade_level = models.CharField(max_length=10, help_text='e.g., Grade 12')
    section = models.CharField(max_length=50, blank=True)
    
    # SF10 Basic Information
    lrn = models.CharField(max_length=20, unique=True, help_text='Learner Reference Number')
    name = models.CharField(max_length=200)
    birth_date = models.DateField()
    birth_place = models.CharField(max_length=200)
    sex = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    age = models.IntegerField()
    
    # Address Information
    present_address = models.TextField()
    permanent_address = models.TextField()
    
    # Contact Information
    contact_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Parent/Guardian Information
    father_name = models.CharField(max_length=200, blank=True)
    father_occupation = models.CharField(max_length=100, blank=True)
    father_contact = models.CharField(max_length=20, blank=True)
    
    mother_name = models.CharField(max_length=200, blank=True)
    mother_occupation = models.CharField(max_length=100, blank=True)
    mother_contact = models.CharField(max_length=20, blank=True)
    
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_relationship = models.CharField(max_length=50, blank=True)
    guardian_contact = models.CharField(max_length=20, blank=True)
    
    # Academic Information
    previous_school = models.CharField(max_length=200, blank=True)
    previous_grade = models.CharField(max_length=20, blank=True)
    date_of_enrollment = models.DateField()
    date_of_graduation = models.DateField(blank=True, null=True)
    
    # Document Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_complete = models.BooleanField(default=False)
    
    # File Management
    excel_file = models.FileField(upload_to='sf10/excel/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='sf10/pdf/', blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_sf10')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'school_year']
    
    def __str__(self):
        return f"SF10 - {self.name} ({self.school_year})"
    
    @property
    def full_name(self):
        return self.name
    
    @property
    def is_transferred(self):
        return self.status == 'transferred'

class SF10Grade(models.Model):
    """SF10 Grade Records"""
    sf10_document = models.ForeignKey(SF10Document, on_delete=models.CASCADE, related_name='grades')
    subject = models.CharField(max_length=100)
    first_quarter = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    second_quarter = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    third_quarter = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    fourth_quarter = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    remarks = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['subject']
    
    def __str__(self):
        return f"{self.subject} - {self.sf10_document.name}"

class SF10Attendance(models.Model):
    """SF10 Attendance Records"""
    sf10_document = models.ForeignKey(SF10Document, on_delete=models.CASCADE, related_name='attendance')
    month = models.CharField(max_length=20)
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    days_tardy = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['month']
    
    def __str__(self):
        return f"{self.month} - {self.sf10_document.name}"

class SF10Upload(models.Model):
    """SF10 Excel Upload Tracking"""
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=200)
    excel_file = models.FileField(upload_to='sf10/uploads/')
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    error_log = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"SF10 Upload: {self.name} ({self.status})"
