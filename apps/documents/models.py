from django.db import models
from django.contrib.auth import get_user_model
from apps.accounts.models import User
from apps.students.models import Student

User = get_user_model()

# SF10 models are imported separately to avoid circular imports

class DocumentCategory(models.Model):
    """Document categories for organization"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Document Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class DocumentType(models.Model):
    """Types of documents (Certificate, Transcript, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='document_types')
    requires_verification = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"

class StudentDocument(models.Model):
    """Student documents with claim tracking"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('claimed', 'Claimed'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
        ('archived', 'Archived'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='document_records')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    document_number = models.CharField(max_length=50, unique=True, help_text='Unique document number')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Document file
    file = models.FileField(upload_to='documents/student_docs/', blank=True, null=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    date_created = models.DateField(auto_now_add=True)
    date_issued = models.DateField(blank=True, null=True)
    date_claimed = models.DateField(blank=True, null=True)
    
    # Claim information
    claimed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_documents')
    claimed_by_name = models.CharField(max_length=200, blank=True, help_text='Name of person who claimed')
    claimed_by_relation = models.CharField(max_length=50, blank=True, help_text='Relationship to student')
    claimed_by_id_number = models.CharField(max_length=50, blank=True, help_text='ID number of claimant')
    claim_remarks = models.TextField(blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_documents')
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_created', 'student__user__last_name']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['document_type']),
            models.Index(fields=['date_created']),
        ]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.title}"
    
    @property
    def is_claimable(self):
        return self.status == 'available'
    
    @property
    def is_claimed(self):
        return self.status == 'claimed'
    
    @property
    def days_since_created(self):
        from datetime import date
        return (date.today() - self.date_created).days

class DocumentClaim(models.Model):
    """Track document claims"""
    document = models.ForeignKey(StudentDocument, on_delete=models.CASCADE, related_name='claims')
    claimed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_claims')
    claimed_by_name = models.CharField(max_length=200)
    claimed_by_relation = models.CharField(max_length=50)
    claimed_by_id_number = models.CharField(max_length=50)
    claim_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-claim_date']
    
    def __str__(self):
        return f"{self.document} - Claimed by {self.claimed_by_name}"

class DocumentBatch(models.Model):
    """For importing documents from Excel"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    excel_file = models.FileField(upload_to='documents/batches/')
    total_documents = models.IntegerField(default=0)
    imported_documents = models.IntegerField(default=0)
    failed_imports = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Batch: {self.name} ({self.imported_documents}/{self.total_documents})"
