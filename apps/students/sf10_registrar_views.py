"""
SF10 Document Management Views for Registrar
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import date, timedelta
import io
import csv

# Optional pandas import for Excel functionality
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except (ImportError, ValueError):
    PANDAS_AVAILABLE = False

from apps.documents.sf10_models import SF10Document, SF10Grade, SF10Attendance, SF10Upload
from apps.documents.sf10_forms import (
    SF10DocumentForm, SF10GradeForm, SF10AttendanceForm, 
    SF10UploadForm, SF10SearchForm
)
from apps.students.models import Student
from .models import Grade, Section

def is_admin_or_registrar(user):
    """Check if user is admin or registrar"""
    return user.is_authenticated and (user.is_superuser or user.role == 'ADMIN')

@login_required
def sf10_dashboard(request):
    """SF10 Document Management Dashboard for Registrar"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    # Statistics
    total_sf10 = SF10Document.objects.count()
    active_sf10 = SF10Document.objects.filter(status='active').count()
    transferred_sf10 = SF10Document.objects.filter(status='transferred').count()
    complete_sf10 = SF10Document.objects.filter(is_complete=True).count()
    
    # Recent SF10 documents
    recent_sf10 = SF10Document.objects.select_related(
        'student__user', 'created_by'
    ).order_by('-created_at')[:10]
    
    # Status distribution
    status_stats = SF10Document.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Grade level distribution
    grade_stats = SF10Document.objects.values('grade_level').annotate(
        count=Count('id')
    ).order_by('grade_level')
    
    # School year distribution
    year_stats = SF10Document.objects.values('school_year').annotate(
        count=Count('id')
    ).order_by('-school_year')
    
    context = {
        'total_sf10': total_sf10,
        'active_sf10': active_sf10,
        'transferred_sf10': transferred_sf10,
        'complete_sf10': complete_sf10,
        'recent_sf10': recent_sf10,
        'status_stats': status_stats,
        'grade_stats': grade_stats,
        'year_stats': year_stats,
        'pandas_available': PANDAS_AVAILABLE,
    }
    
    return render(request, 'students/sf10_dashboard.html', context)

@login_required
def sf10_list(request):
    """List all SF10 documents with search and filters"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    # Search and filters
    search_form = SF10SearchForm(request.GET)
    sf10_documents = SF10Document.objects.select_related('student__user', 'created_by')
    
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        school_year = search_form.cleaned_data.get('school_year')
        grade_level = search_form.cleaned_data.get('grade_level')
        status = search_form.cleaned_data.get('status')
        
        if search:
            sf10_documents = sf10_documents.filter(
                Q(name__icontains=search) |
                Q(lrn__icontains=search) |
                Q(student__user__first_name__icontains=search) |
                Q(student__user__last_name__icontains=search)
            )
        
        if school_year:
            sf10_documents = sf10_documents.filter(school_year__icontains=school_year)
        
        if grade_level:
            sf10_documents = sf10_documents.filter(grade_level__icontains=grade_level)
        
        if status:
            sf10_documents = sf10_documents.filter(status=status)
    
    # Pagination
    paginator = Paginator(sf10_documents.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'pandas_available': PANDAS_AVAILABLE,
    }
    
    return render(request, 'students/sf10_list.html', context)

@login_required
def sf10_create(request):
    """Create new SF10 document"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = SF10DocumentForm(request.POST)
        if form.is_valid():
            sf10_doc = form.save(commit=False)
            sf10_doc.created_by = request.user
            sf10_doc.save()
            messages.success(request, f'SF10 document for {sf10_doc.name} created successfully.')
            return redirect('registrar:sf10_detail', pk=sf10_doc.pk)
    else:
        form = SF10DocumentForm()
    
    context = {
        'form': form,
        'title': 'Create SF10 Document',
    }
    
    return render(request, 'students/sf10_form.html', context)

@login_required
def sf10_detail(request, pk):
    """View SF10 document details"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    sf10_doc = get_object_or_404(SF10Document, pk=pk)
    grades = sf10_doc.grades.all()
    attendance = sf10_doc.attendance.all()
    
    context = {
        'sf10_doc': sf10_doc,
        'grades': grades,
        'attendance': attendance,
    }
    
    return render(request, 'students/sf10_detail.html', context)

@login_required
def sf10_edit(request, pk):
    """Edit SF10 document"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    sf10_doc = get_object_or_404(SF10Document, pk=pk)
    
    if request.method == 'POST':
        form = SF10DocumentForm(request.POST, instance=sf10_doc)
        if form.is_valid():
            form.save()
            messages.success(request, f'SF10 document for {sf10_doc.name} updated successfully.')
            return redirect('registrar:sf10_detail', pk=sf10_doc.pk)
    else:
        form = SF10DocumentForm(instance=sf10_doc)
    
    context = {
        'form': form,
        'sf10_doc': sf10_doc,
        'title': f'Edit SF10 Document - {sf10_doc.name}',
    }
    
    return render(request, 'students/sf10_form.html', context)

@login_required
def sf10_upload(request):
    """Upload SF10 Excel file"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = SF10UploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.created_by = request.user
            upload.save()
            
            # Process the Excel file
            try:
                if PANDAS_AVAILABLE and upload.excel_file:
                    df = pd.read_excel(upload.excel_file.path)
                    upload.total_records = len(df)
                    upload.status = 'processing'
                    upload.save()
                    
                    # Process each row
                    processed = 0
                    failed = 0
                    errors = []
                    
                    for index, row in df.iterrows():
                        try:
                            # Create or update SF10 document
                            sf10_doc, created = SF10Document.objects.get_or_create(
                                lrn=row.get('LRN', ''),
                                school_year=row.get('School Year', ''),
                                defaults={
                                    'student': Student.objects.get(student_id=row.get('Student ID', '')),
                                    'name': row.get('Name', ''),
                                    'grade_level': row.get('Grade Level', ''),
                                    'section': row.get('Section', ''),
                                    'birth_date': row.get('Birth Date', ''),
                                    'birth_place': row.get('Birth Place', ''),
                                    'sex': row.get('Sex', ''),
                                    'age': row.get('Age', 0),
                                    'present_address': row.get('Present Address', ''),
                                    'permanent_address': row.get('Permanent Address', ''),
                                    'contact_number': row.get('Contact Number', ''),
                                    'email': row.get('Email', ''),
                                    'father_name': row.get('Father Name', ''),
                                    'father_occupation': row.get('Father Occupation', ''),
                                    'father_contact': row.get('Father Contact', ''),
                                    'mother_name': row.get('Mother Name', ''),
                                    'mother_occupation': row.get('Mother Occupation', ''),
                                    'mother_contact': row.get('Mother Contact', ''),
                                    'guardian_name': row.get('Guardian Name', ''),
                                    'guardian_relationship': row.get('Guardian Relationship', ''),
                                    'guardian_contact': row.get('Guardian Contact', ''),
                                    'previous_school': row.get('Previous School', ''),
                                    'previous_grade': row.get('Previous Grade', ''),
                                    'date_of_enrollment': row.get('Date of Enrollment', ''),
                                    'date_of_graduation': row.get('Date of Graduation', ''),
                                    'status': row.get('Status', 'active'),
                                    'is_complete': row.get('Is Complete', False),
                                    'notes': row.get('Notes', ''),
                                    'created_by': request.user,
                                }
                            )
                            
                            if not created:
                                # Update existing record
                                for field in ['name', 'grade_level', 'section', 'birth_date', 'birth_place', 
                                           'sex', 'age', 'present_address', 'permanent_address', 
                                           'contact_number', 'email', 'father_name', 'father_occupation', 
                                           'father_contact', 'mother_name', 'mother_occupation', 
                                           'mother_contact', 'guardian_name', 'guardian_relationship', 
                                           'guardian_contact', 'previous_school', 'previous_grade', 
                                           'date_of_enrollment', 'date_of_graduation', 'status', 
                                           'is_complete', 'notes']:
                                    if field in row and pd.notna(row[field]):
                                        setattr(sf10_doc, field, row[field])
                                sf10_doc.save()
                            
                            processed += 1
                            
                        except Exception as e:
                            failed += 1
                            errors.append(f"Row {index + 1}: {str(e)}")
                    
                    upload.processed_records = processed
                    upload.failed_records = failed
                    upload.status = 'completed' if failed == 0 else 'failed'
                    upload.error_log = '\n'.join(errors)
                    upload.completed_at = timezone.now()
                    upload.save()
                    
                    messages.success(request, f'Upload completed! Processed: {processed}, Failed: {failed}')
                else:
                    messages.error(request, 'Pandas is not available for Excel processing.')
                    
            except Exception as e:
                upload.status = 'failed'
                upload.error_log = str(e)
                upload.save()
                messages.error(request, f'Error processing file: {str(e)}')
            
            return redirect('registrar:sf10_upload')
    else:
        form = SF10UploadForm()
    
    # Get recent uploads
    recent_uploads = SF10Upload.objects.filter(created_by=request.user).order_by('-created_at')[:10]
    
    context = {
        'form': form,
        'recent_uploads': recent_uploads,
        'pandas_available': PANDAS_AVAILABLE,
    }
    
    return render(request, 'students/sf10_upload.html', context)

@login_required
def sf10_download_template(request):
    """Download SF10 Excel template"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    if PANDAS_AVAILABLE:
        # Create template DataFrame
        template_data = {
            'Student ID': ['STU001', 'STU002'],
            'LRN': ['123456789012', '123456789013'],
            'Name': ['John Doe', 'Jane Smith'],
            'School Year': ['2023-2024', '2023-2024'],
            'Grade Level': ['Grade 12', 'Grade 12'],
            'Section': ['STEM A', 'STEM B'],
            'Birth Date': ['2005-01-15', '2005-03-20'],
            'Birth Place': ['Manila', 'Quezon City'],
            'Sex': ['M', 'F'],
            'Age': [18, 18],
            'Present Address': ['123 Main St, Manila', '456 Oak Ave, QC'],
            'Permanent Address': ['123 Main St, Manila', '456 Oak Ave, QC'],
            'Contact Number': ['09123456789', '09123456790'],
            'Email': ['john@email.com', 'jane@email.com'],
            'Father Name': ['John Doe Sr.', 'Jane Smith Sr.'],
            'Father Occupation': ['Engineer', 'Teacher'],
            'Father Contact': ['09123456791', '09123456792'],
            'Mother Name': ['Mary Doe', 'Mary Smith'],
            'Mother Occupation': ['Nurse', 'Doctor'],
            'Mother Contact': ['09123456793', '09123456794'],
            'Guardian Name': ['', ''],
            'Guardian Relationship': ['', ''],
            'Guardian Contact': ['', ''],
            'Previous School': ['ABC High School', 'XYZ High School'],
            'Previous Grade': ['Grade 11', 'Grade 11'],
            'Date of Enrollment': ['2023-06-01', '2023-06-01'],
            'Date of Graduation': ['', ''],
            'Status': ['active', 'active'],
            'Is Complete': [True, False],
            'Notes': ['Sample record 1', 'Sample record 2'],
        }
        
        df = pd.DataFrame(template_data)
        
        # Create Excel response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="sf10_template.xlsx"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='SF10 Template', index=False)
        
        return response
    else:
        # Fallback to CSV template
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sf10_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Student ID', 'LRN', 'Name', 'School Year', 'Grade Level', 'Section',
            'Birth Date', 'Birth Place', 'Sex', 'Age', 'Present Address', 'Permanent Address',
            'Contact Number', 'Email', 'Father Name', 'Father Occupation', 'Father Contact',
            'Mother Name', 'Mother Occupation', 'Mother Contact', 'Guardian Name',
            'Guardian Relationship', 'Guardian Contact', 'Previous School', 'Previous Grade',
            'Date of Enrollment', 'Date of Graduation', 'Status', 'Is Complete', 'Notes'
        ])
        
        # Add sample data
        writer.writerow([
            'STU001', '123456789012', 'John Doe', '2023-2024', 'Grade 12', 'STEM A',
            '2005-01-15', 'Manila', 'M', 18, '123 Main St, Manila', '123 Main St, Manila',
            '09123456789', 'john@email.com', 'John Doe Sr.', 'Engineer', '09123456791',
            'Mary Doe', 'Nurse', '09123456793', '', '', '', 'ABC High School', 'Grade 11',
            '2023-06-01', '', 'active', 'True', 'Sample record 1'
        ])
        
        return response

@login_required
def sf10_statistics(request):
    """SF10 Statistics and Analytics"""
    if not is_admin_or_registrar(request.user):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('accounts:login')
    
    # Basic statistics
    total_sf10 = SF10Document.objects.count()
    active_sf10 = SF10Document.objects.filter(status='active').count()
    transferred_sf10 = SF10Document.objects.filter(status='transferred').count()
    complete_sf10 = SF10Document.objects.filter(is_complete=True).count()
    
    # Status distribution
    status_distribution = SF10Document.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Grade level distribution
    grade_distribution = SF10Document.objects.values('grade_level').annotate(
        count=Count('id')
    ).order_by('grade_level')
    
    # School year distribution
    year_distribution = SF10Document.objects.values('school_year').annotate(
        count=Count('id')
    ).order_by('-school_year')
    
    # Recent activity
    recent_activity = SF10Document.objects.select_related(
        'student__user', 'created_by'
    ).order_by('-created_at')[:20]
    
    context = {
        'total_sf10': total_sf10,
        'active_sf10': active_sf10,
        'transferred_sf10': transferred_sf10,
        'complete_sf10': complete_sf10,
        'status_distribution': status_distribution,
        'grade_distribution': grade_distribution,
        'year_distribution': year_distribution,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'students/sf10_statistics.html', context)
