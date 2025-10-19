from django.contrib import admin
from .models import AcademicYear, Grade, Section, Student, Attendance, StudentDocument


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current', 'created_at')
    list_filter = ('is_current', 'created_at')
    search_fields = ('name',)
    ordering = ('-start_date',)


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'capacity', 'current_students_count', 'available_seats', 'is_active')
    list_filter = ('grade', 'is_active', 'created_at')
    search_fields = ('name', 'grade__name')
    ordering = ('grade', 'name')
    
    def current_students_count(self, obj):
        return obj.current_students_count
    current_students_count.short_description = 'Current Students'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'grade', 'section', 'academic_year', 'gender', 'is_active', 'created_at')
    list_filter = ('grade', 'section', 'academic_year', 'gender', 'is_active', 'created_at')
    search_fields = ('student_id', 'admission_number', 'user__first_name', 'user__last_name', 'parent_name')
    ordering = ('student_id',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'student_id', 'admission_number', 'admission_date', 'gender', 'date_of_birth', 'blood_group')
        }),
        ('Academic Information', {
            'fields': ('grade', 'section', 'academic_year')
        }),
        ('Parent Information', {
            'fields': ('parent_name', 'parent_phone', 'parent_email')
        }),
        ('Contact Information', {
            'fields': ('address', 'emergency_contact', 'emergency_phone')
        }),
        ('Medical Information', {
            'fields': ('medical_conditions',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'marked_by', 'created_at')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__student_id')
    ordering = ('-date', 'student__student_id')
    date_hierarchy = 'date'


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ('student', 'document_type', 'title', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'title')
    ordering = ('-uploaded_at',)
