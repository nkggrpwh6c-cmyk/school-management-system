"""
Registrar-specific views for comprehensive student management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import csv
from io import StringIO
from .models import Student, StudentDocument, Attendance
from .bulk_import import StudentBulkImporter
from .bulk_forms import BulkImportForm
from django.contrib.auth import get_user_model

User = get_user_model()


def is_registrar(user):
    """Check if user is registrar"""
    return (user.is_authenticated and 
            (user.username == 'crenz' or 
             user.role == 'ADMIN' or 
             user.is_staff))


@login_required
@user_passes_test(is_registrar)
def registrar_dashboard(request):
    """Main registrar dashboard"""
    
    # Get statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    graduated_students = Student.objects.filter(is_active=False).count()
    transferred_students = 0  # Will be implemented later
    
    # Grade level distribution
    grade_distribution = Student.objects.filter(is_active=True).values('grade__name').annotate(
        count=Count('grade__name')
    ).order_by('grade__name')
    
    # Recent activities (simplified for now)
    recent_activities = []
    
    # Recent documents
    recent_documents = StudentDocument.objects.select_related('student').order_by('-uploaded_at')[:5]
    
    # Students by section
    section_distribution = Student.objects.filter(is_active=True).values(
        'grade__name', 'section__name'
    ).annotate(
        count=Count('id')
    ).order_by('grade__name', 'section__name')
    
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'graduated_students': graduated_students,
        'transferred_students': transferred_students,
        'grade_distribution': grade_distribution,
        'section_distribution': section_distribution,
        'recent_activities': recent_activities,
        'recent_documents': recent_documents,
    }
    
    return render(request, 'students/registrar_dashboard.html', context)


@login_required
@user_passes_test(is_registrar)
def student_search(request):
    """Advanced student search with filters"""
    
    query = request.GET.get('q', '')
    grade_level = request.GET.get('grade_level', '')
    section = request.GET.get('section', '')
    status = request.GET.get('status', '')
    strand = request.GET.get('strand', '')
    
    students = Student.objects.all()
    
    # Apply filters
    if query:
        students = students.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(student_id__icontains=query) |
            Q(user__email__icontains=query) |
            Q(parent_name__icontains=query)
        )
    
    if grade_level:
        students = students.filter(grade__name=grade_level)
    
    if section:
        students = students.filter(section__name__icontains=section)
    
    if status:
        students = students.filter(is_active=(status == 'ACTIVE'))
    
    if strand:
        students = students.filter(section__name__icontains=strand)
    
    # Pagination
    paginator = Paginator(students.order_by('user__last_name', 'user__first_name'), 25)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    
    # Get filter options
    grade_levels = Student.objects.values_list('grade__name', flat=True).distinct().order_by('grade__name')
    sections = Student.objects.values_list('section__name', flat=True).distinct().order_by('section__name')
    strands = []  # Will be implemented later
    statuses = [('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]
    
    context = {
        'students': students,
        'query': query,
        'grade_level': grade_level,
        'section': section,
        'status': status,
        'strand': strand,
        'grade_levels': grade_levels,
        'sections': sections,
        'strands': strands,
        'statuses': statuses,
    }
    
    return render(request, 'students/student_search.html', context)


@login_required
@user_passes_test(is_registrar)
def student_detail(request, student_id):
    """Detailed student profile view"""
    
    student = get_object_or_404(Student, student_id=student_id)
    
    # Get student documents
    documents = student.documents.all().order_by('-uploaded_at')
    
    # Get student grades (simplified for now)
    grades = []
    
    # Get audit log (simplified for now)
    audit_log = []
    
    # Get access log (simplified for now)
    access_log = []
    
    context = {
        'student': student,
        'documents': documents,
        'grades': grades,
        'audit_log': audit_log,
        'access_log': access_log,
    }
    
    return render(request, 'students/student_detail.html', context)


@login_required
@user_passes_test(is_registrar)
def student_edit(request, student_id):
    """Edit student information"""
    
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        # Update student information
        form_data = request.POST
        
        # Update basic fields
        if 'parent_name' in form_data:
            student.parent_name = form_data['parent_name']
        if 'parent_phone' in form_data:
            student.parent_phone = form_data['parent_phone']
        if 'parent_email' in form_data:
            student.parent_email = form_data['parent_email']
        if 'address' in form_data:
            student.address = form_data['address']
        if 'emergency_contact' in form_data:
            student.emergency_contact = form_data['emergency_contact']
        if 'emergency_phone' in form_data:
            student.emergency_phone = form_data['emergency_phone']
        if 'medical_conditions' in form_data:
            student.medical_conditions = form_data['medical_conditions']
        
        student.save()
        
        messages.success(request, f'Student {student.user.get_full_name()} updated successfully!')
        return redirect('students:student_detail', student_id=student_id)
    
    context = {
        'student': student,
    }
    
    return render(request, 'students/student_edit.html', context)


@login_required
@user_passes_test(is_registrar)
def document_upload(request, student_id):
    """Upload document for student"""
    
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        file = request.FILES.get('file')
        
        if document_type and title and file:
            document = StudentDocument.objects.create(
                student=student,
                document_type=document_type,
                title=title,
                description=description,
                file=file
            )
            
            messages.success(request, f'Document "{title}" uploaded successfully!')
            return redirect('students:student_detail', student_id=student_id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'student': student,
        'document_types': StudentDocument.DOCUMENT_TYPES,
    }
    
    return render(request, 'students/document_upload.html', context)


@login_required
@user_passes_test(is_registrar)
def bulk_import_registrar(request):
    """Bulk import interface for registrar"""
    
    if request.method == 'POST':
        form = BulkImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            file = form.cleaned_data['file']
            grade_level = form.cleaned_data.get('grade_level')
            section = form.cleaned_data.get('section')
            
            # Initialize importer
            importer = StudentBulkImporter()
            
            # Apply default values if provided
            if grade_level or section:
                content = file.read().decode('utf-8')
                csv_reader = csv.DictReader(StringIO(content))
                rows = list(csv_reader)
                
                for row in rows:
                    if grade_level and not row.get('grade_level'):
                        row['grade_level'] = grade_level
                    if section and not row.get('section'):
                        row['section'] = section
                
                output = StringIO()
                if rows:
                    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
                    content = output.getvalue()
                
                file = ContentFile(content.encode('utf-8'))
            
            # Import and validate
            if importer.import_students(file):
                # Store import data in session for preview
                request.session['bulk_import_data'] = {
                    'file_name': file.name,
                    'import_data': importer.import_data,
                    'errors': importer.errors,
                    'success_count': importer.success_count,
                }
                
                return redirect('students:bulk_import_preview_registrar')
            else:
                messages.error(request, 'Error processing file. Please check the file format.')
    else:
        form = BulkImportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'students/bulk_import_registrar.html', context)


@login_required
@user_passes_test(is_registrar)
def bulk_import_preview_registrar(request):
    """Preview bulk import for registrar"""
    
    import_data = request.session.get('bulk_import_data')
    if not import_data:
        messages.error(request, 'No import data found. Please upload a file first.')
        return redirect('students:bulk_import_registrar')
    
    if request.method == 'POST':
        if request.POST.get('confirm_import'):
            # Process the import
            importer = StudentBulkImporter()
            importer.import_data = import_data['import_data']
            importer.errors = import_data['errors']
            
            try:
                with transaction.atomic():
                    created_students = importer.create_students()
                    
                    # Log the bulk import (simplified for now)
                    pass
                    
                    messages.success(request, f'Successfully imported {len(created_students)} students!')
                    
                    # Clear session data
                    del request.session['bulk_import_data']
                    
                    return redirect('students:registrar_dashboard')
                    
            except Exception as e:
                messages.error(request, f'Error during import: {str(e)}')
    
    context = {
        'import_data': import_data,
        'preview_data': import_data['import_data'][:10],
        'total_rows': len(import_data['import_data']),
        'error_count': len(import_data['errors']),
        'success_count': import_data['success_count']
    }
    
    return render(request, 'students/bulk_import_preview_registrar.html', context)


@login_required
@user_passes_test(is_registrar)
def export_students(request):
    """Export students to CSV"""
    
    # Get filter parameters
    grade_level = request.GET.get('grade_level', '')
    section = request.GET.get('section', '')
    status = request.GET.get('status', '')
    
    students = Student.objects.all()
    
    if grade_level:
        students = students.filter(grade__name=grade_level)
    if section:
        students = students.filter(section__name__icontains=section)
    if status:
        students = students.filter(is_active=(status == 'ACTIVE'))
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'First Name', 'Last Name', 'Email', 'Grade', 'Section',
        'Status', 'Address', 'Parent Name', 'Parent Phone', 'Parent Email',
        'Emergency Contact', 'Emergency Phone', 'Medical Conditions'
    ])
    
    for student in students:
        writer.writerow([
            student.student_id, student.user.first_name, student.user.last_name,
            student.user.email, student.grade.name, student.section.name,
            'Active' if student.is_active else 'Inactive', student.address,
            student.parent_name, student.parent_phone, student.parent_email,
            student.emergency_contact, student.emergency_phone, student.medical_conditions
        ])
    
    return response


@login_required
@user_passes_test(is_registrar)
def student_analytics(request):
    """Student analytics and reports"""
    
    # Get statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    
    # Grade distribution
    grade_distribution = Student.objects.filter(is_active=True).values('grade__name').annotate(
        count=Count('id')
    ).order_by('grade__name')
    
    # Status distribution
    status_distribution = [
        {'status': 'ACTIVE', 'count': Student.objects.filter(is_active=True).count()},
        {'status': 'INACTIVE', 'count': Student.objects.filter(is_active=False).count()}
    ]
    
    # Recent activities (simplified for now)
    recent_activities = []
    
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'grade_distribution': grade_distribution,
        'status_distribution': status_distribution,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'students/student_analytics.html', context)
