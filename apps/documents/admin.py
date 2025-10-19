from django.contrib import admin
from .models import DocumentCategory, DocumentType, StudentDocument, DocumentClaim, DocumentBatch

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'requires_verification', 'is_active']
    list_filter = ['category', 'requires_verification', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']

@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ['student', 'title', 'document_type', 'status', 'date_created', 'date_claimed']
    list_filter = ['status', 'document_type', 'date_created', 'is_verified']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'title', 'document_number']
    readonly_fields = ['date_created', 'updated_at']
    ordering = ['-date_created']
    
    fieldsets = (
        ('Document Information', {
            'fields': ('student', 'document_type', 'title', 'description', 'document_number')
        }),
        ('File', {
            'fields': ('file',)
        }),
        ('Status & Tracking', {
            'fields': ('status', 'date_issued', 'date_claimed', 'is_verified')
        }),
        ('Claim Information', {
            'fields': ('claimed_by', 'claimed_by_name', 'claimed_by_relation', 'claimed_by_id_number', 'claim_remarks')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at')
        }),
        ('Metadata', {
            'fields': ('created_by', 'date_created', 'updated_at', 'notes')
        }),
    )

@admin.register(DocumentClaim)
class DocumentClaimAdmin(admin.ModelAdmin):
    list_display = ['document', 'claimed_by_name', 'claimed_by_relation', 'claim_date']
    list_filter = ['claim_date']
    search_fields = ['document__title', 'claimed_by_name']
    ordering = ['-claim_date']

@admin.register(DocumentBatch)
class DocumentBatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_documents', 'imported_documents', 'failed_imports', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

# SF10 Admin Classes - Imported separately to avoid circular imports
try:
    from .sf10_models import SF10Document, SF10Grade, SF10Attendance, SF10Upload
    
    @admin.register(SF10Document)
    class SF10DocumentAdmin(admin.ModelAdmin):
        list_display = ['name', 'lrn', 'school_year', 'grade_level', 'status', 'is_complete', 'created_at']
        list_filter = ['status', 'is_complete', 'school_year', 'grade_level', 'created_at']
        search_fields = ['name', 'lrn', 'school_year', 'student__user__first_name', 'student__user__last_name']
        readonly_fields = ['created_at', 'updated_at']
        ordering = ['-created_at']
        
        fieldsets = (
            ('Basic Information', {
                'fields': ('student', 'school_year', 'grade_level', 'section', 'lrn', 'name', 'birth_date', 'birth_place', 'sex', 'age')
            }),
            ('Address Information', {
                'fields': ('present_address', 'permanent_address', 'contact_number', 'email')
            }),
            ('Parent/Guardian Information', {
                'fields': ('father_name', 'father_occupation', 'father_contact', 'mother_name', 'mother_occupation', 'mother_contact', 'guardian_name', 'guardian_relationship', 'guardian_contact')
            }),
            ('Academic Information', {
                'fields': ('previous_school', 'previous_grade', 'date_of_enrollment', 'date_of_graduation')
            }),
            ('Document Status', {
                'fields': ('status', 'is_complete', 'excel_file', 'pdf_file')
            }),
            ('Metadata', {
                'fields': ('created_by', 'created_at', 'updated_at', 'notes')
            }),
        )

    @admin.register(SF10Grade)
    class SF10GradeAdmin(admin.ModelAdmin):
        list_display = ['sf10_document', 'subject', 'first_quarter', 'second_quarter', 'third_quarter', 'fourth_quarter', 'final_grade']
        list_filter = ['sf10_document__school_year', 'sf10_document__grade_level']
        search_fields = ['subject', 'sf10_document__name']
        ordering = ['sf10_document', 'subject']

    @admin.register(SF10Attendance)
    class SF10AttendanceAdmin(admin.ModelAdmin):
        list_display = ['sf10_document', 'month', 'days_present', 'days_absent', 'days_tardy']
        list_filter = ['sf10_document__school_year', 'month']
        search_fields = ['month', 'sf10_document__name']
        ordering = ['sf10_document', 'month']

    @admin.register(SF10Upload)
    class SF10UploadAdmin(admin.ModelAdmin):
        list_display = ['name', 'status', 'total_records', 'processed_records', 'failed_records', 'created_at']
        list_filter = ['status', 'created_at']
        search_fields = ['name']
        readonly_fields = ['created_at', 'completed_at']
        ordering = ['-created_at']
        
except ImportError:
    pass  # SF10 models not available yet
