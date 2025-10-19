"""
Views for bulk import functionality
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
import io
import json
import os
import csv
try:
    import pandas as pd
except ImportError:
    pd = None
from .simple_bulk_import import SimpleStudentBulkImporter
from .bulk_forms import BulkImportForm, ImportPreviewForm, ImportTemplateForm
from .models import Student
from django.contrib.auth import get_user_model

User = get_user_model()


def is_admin_or_registrar(user):
    """Check if user is admin or registrar"""
    return (user.is_authenticated and 
            (user.is_staff or 
             user.role == 'ADMIN' or 
             user.role == 'TEACHER'))


@login_required
@user_passes_test(is_admin_or_registrar)
def bulk_import_dashboard(request):
    """Main bulk import dashboard"""
    
    # Simple bulk import is always available
    
    # Get recent imports
    recent_imports = Student.objects.filter(
        created_at__gte=timezone.now().replace(day=1)
    ).order_by('-created_at')[:10]
    
    # Get statistics
    total_students = Student.objects.count()
    students_this_month = Student.objects.filter(
        created_at__gte=timezone.now().replace(day=1)
    ).count()
    
    context = {
        'recent_imports': recent_imports,
        'total_students': total_students,
        'students_this_month': students_this_month,
    }
    
    return render(request, 'students/bulk_import_dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_registrar)
def bulk_import_upload(request):
    """Handle file upload and validation"""
    
    if request.method == 'POST':
        form = BulkImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            file = form.cleaned_data['file']
            grade_level = form.cleaned_data.get('grade_level')
            section = form.cleaned_data.get('section')
            send_credentials = form.cleaned_data.get('send_credentials', False)
            
            # Initialize importer
            importer = SimpleStudentBulkImporter()
            
            # Apply default values if provided (for CSV only)
            if grade_level or section:
                # Read CSV content
                content = file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(content))
                rows = list(csv_reader)
                
                # Apply defaults
                for row in rows:
                    if grade_level and not row.get('grade_level'):
                        row['grade_level'] = grade_level
                    if section and not row.get('section'):
                        row['section'] = section
                
                # Create new CSV content
                output = io.StringIO()
                if rows:
                    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
                    content = output.getvalue()
                
                # Update file content
                file = io.BytesIO(content.encode('utf-8'))
            
            # Import and validate
            if importer.import_students(file):
                # Store import data in session for preview
                request.session['bulk_import_data'] = {
                    'file_name': file.name,
                    'import_data': importer.import_data,
                    'errors': importer.errors,
                    'success_count': importer.success_count,
                    'send_credentials': send_credentials
                }
                
                return redirect('students:bulk_import_preview')
            else:
                messages.error(request, 'Error processing file. Please check the file format.')
    else:
        form = BulkImportForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'students/bulk_import_upload.html', context)


@login_required
@user_passes_test(is_admin_or_registrar)
def bulk_import_preview(request):
    """Preview import data before confirmation"""
    
    import_data = request.session.get('bulk_import_data')
    if not import_data:
        messages.error(request, 'No import data found. Please upload a file first.')
        return redirect('students:bulk_import_upload')
    
    if request.method == 'POST':
        form = ImportPreviewForm(request.POST)
        
        if form.is_valid() and form.cleaned_data['confirm_import']:
            # Process the import
            importer = SimpleStudentBulkImporter()
            importer.import_data = import_data['import_data']
            importer.errors = import_data['errors']
            
            try:
                with transaction.atomic():
                    created_students = importer.create_students()
                    
                    # Send credentials if requested
                    if import_data.get('send_credentials'):
                        # TODO: Implement email sending
                        pass
                    
                    messages.success(
                        request, 
                        f'Successfully imported {len(created_students)} students!'
                    )
                    
                    # Clear session data
                    del request.session['bulk_import_data']
                    
                    return redirect('students:bulk_import_success', 
                                 success_count=len(created_students))
                    
            except Exception as e:
                messages.error(request, f'Error during import: {str(e)}')
        else:
            messages.error(request, 'Please confirm the import to proceed.')
    
    else:
        form = ImportPreviewForm()
    
    context = {
        'form': form,
        'import_data': import_data,
        'preview_data': import_data['import_data'][:10],  # Show first 10 rows
        'total_rows': len(import_data['import_data']),
        'error_count': len(import_data['errors']),
        'success_count': import_data['success_count']
    }
    
    return render(request, 'students/bulk_import_preview.html', context)


@login_required
@user_passes_test(is_admin_or_registrar)
def bulk_import_success(request, success_count):
    """Show import success page"""
    
    context = {
        'success_count': success_count,
    }
    
    return render(request, 'students/bulk_import_success.html', context)


@login_required
@user_passes_test(is_admin_or_registrar)
def download_template(request):
    """Download import template"""
    
    if request.method == 'POST':
        form = ImportTemplateForm(request.POST)
        
        if form.is_valid():
            template_type = form.cleaned_data['template_type']
            grade_level = form.cleaned_data.get('grade_level')
            section = form.cleaned_data.get('section')
            
            # Create template data
            if template_type == 'basic':
                columns = SimpleStudentBulkImporter.REQUIRED_COLUMNS
                sample_data = [
                    ['John', 'Doe', 'john.doe@email.com', '123456789012', '7', 'A'],
                    ['Jane', 'Smith', 'jane.smith@email.com', '123456789013', '7', 'A'],
                ]
            elif template_type == 'complete':
                columns = SimpleStudentBulkImporter.REQUIRED_COLUMNS + [
                    'middle_name', 'date_of_birth', 'gender', 'address', 'phone_number',
                    'parent_name', 'parent_phone', 'parent_email', 'emergency_contact',
                    'emergency_phone', 'blood_type', 'medical_conditions', 'allergies'
                ]
                sample_data = [
                    ['John', 'Doe', 'john.doe@email.com', '123456789012', '7', 'A',
                     'Michael', '2005-01-15', 'Male', '123 Main St', '09123456789',
                     'John Doe Sr.', '09123456788', 'parent@email.com', 'Emergency Contact',
                     '09123456787', 'O+', 'None', 'None'],
                    ['Jane', 'Smith', 'jane.smith@email.com', '123456789013', '7', 'A',
                     'Marie', '2005-03-20', 'Female', '456 Oak Ave', '09123456790',
                     'Jane Smith Sr.', '09123456791', 'parent2@email.com', 'Emergency Contact 2',
                     '09123456792', 'A+', 'Asthma', 'Peanuts'],
                ]
            else:  # sample
                columns = SimpleStudentBulkImporter.REQUIRED_COLUMNS + [
                    'middle_name', 'date_of_birth', 'gender', 'address', 'phone_number',
                    'parent_name', 'parent_phone', 'parent_email', 'emergency_contact',
                    'emergency_phone', 'blood_type', 'medical_conditions', 'allergies'
                ]
                sample_data = [
                    ['John', 'Doe', 'john.doe@email.com', '123456789012', '7', 'A',
                     'Michael', '2005-01-15', 'Male', '123 Main St', '09123456789',
                     'John Doe Sr.', '09123456788', 'parent@email.com', 'Emergency Contact',
                     '09123456787', 'O+', 'None', 'None'],
                    ['Jane', 'Smith', 'jane.smith@email.com', '123456789013', '7', 'A',
                     'Marie', '2005-03-20', 'Female', '456 Oak Ave', '09123456790',
                     'Jane Smith Sr.', '09123456791', 'parent2@email.com', 'Emergency Contact 2',
                     '09123456792', 'A+', 'Asthma', 'Peanuts'],
                    ['Mike', 'Johnson', 'mike.johnson@email.com', '123456789014', '7', 'B',
                     'James', '2005-05-10', 'Male', '789 Pine St', '09123456793',
                     'Mike Johnson Sr.', '09123456794', 'parent3@email.com', 'Emergency Contact 3',
                     '09123456795', 'B+', 'None', 'None'],
                ]
            
            # Apply defaults if provided
            if grade_level:
                for row in sample_data:
                    if len(row) > 4:  # grade_level is at index 4
                        row[4] = grade_level
            
            if section:
                for row in sample_data:
                    if len(row) > 5:  # section is at index 5
                        row[5] = section
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="student_import_template_{template_type}.csv"'
            
            # Write CSV
            writer = csv.writer(response)
            writer.writerow(columns)
            writer.writerows(sample_data)
            
            return response
    
    else:
        form = ImportTemplateForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'students/download_template.html', context)


@login_required
@user_passes_test(is_admin_or_registrar)
def bulk_import_history(request):
    """View import history"""
    
    # Get recent imports (this would need to be tracked in a separate model)
    # For now, we'll show recent students
    recent_students = Student.objects.order_by('-created_at')[:50]
    
    context = {
        'recent_students': recent_students,
    }
    
    return render(request, 'students/bulk_import_history.html', context)
