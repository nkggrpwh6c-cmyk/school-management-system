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

# Optional pandas import for Excel functionality
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except (ImportError, ValueError):
    PANDAS_AVAILABLE = False

from .sf10_models import SF10Document, SF10Grade, SF10Attendance, SF10Upload
from .sf10_forms import (
    SF10DocumentForm, SF10GradeForm, SF10AttendanceForm, 
    SF10UploadForm, SF10SearchForm
)
from apps.students.models import Student

class SF10DashboardView(LoginRequiredMixin, ListView):
    """SF10 Document Management Dashboard"""
    model = SF10Document
    template_name = 'documents/sf10/dashboard.html'
    context_object_name = 'sf10_documents'
    paginate_by = 20
    
    def get_queryset(self):
        return SF10Document.objects.select_related('student__user', 'created_by').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        total_sf10 = SF10Document.objects.count()
        active_sf10 = SF10Document.objects.filter(status='active').count()
        transferred_sf10 = SF10Document.objects.filter(status='transferred').count()
        complete_sf10 = SF10Document.objects.filter(is_complete=True).count()
        
        # Recent SF10 documents
        recent_sf10 = SF10Document.objects.select_related(
            'student__user'
        ).order_by('-created_at')[:10]
        
        # Status distribution
        status_stats = SF10Document.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        context.update({
            'total_sf10': total_sf10,
            'active_sf10': active_sf10,
            'transferred_sf10': transferred_sf10,
            'complete_sf10': complete_sf10,
            'recent_sf10': recent_sf10,
            'status_stats': status_stats,
        })
        
        return context

class SF10ListView(LoginRequiredMixin, ListView):
    """List all SF10 documents with search and filters"""
    model = SF10Document
    template_name = 'documents/sf10/sf10_list.html'
    context_object_name = 'sf10_documents'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = SF10Document.objects.select_related(
            'student__user', 'created_by'
        ).order_by('-created_at')
        
        # Apply search filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(lrn__icontains=search) |
                Q(school_year__icontains=search) |
                Q(student__user__first_name__icontains=search) |
                Q(student__user__last_name__icontains=search)
            )
        
        school_year = self.request.GET.get('school_year')
        if school_year:
            queryset = queryset.filter(school_year__icontains=school_year)
        
        grade_level = self.request.GET.get('grade_level')
        if grade_level:
            queryset = queryset.filter(grade_level__icontains=grade_level)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SF10SearchForm(self.request.GET)
        return context

class SF10DetailView(LoginRequiredMixin, DetailView):
    """View SF10 document details"""
    model = SF10Document
    template_name = 'documents/sf10/sf10_detail.html'
    context_object_name = 'sf10_document'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sf10_document = self.get_object()
        context['grades'] = sf10_document.grades.all().order_by('subject')
        context['attendance'] = sf10_document.attendance.all().order_by('month')
        return context

class SF10CreateView(LoginRequiredMixin, CreateView):
    """Create new SF10 document"""
    model = SF10Document
    form_class = SF10DocumentForm
    template_name = 'documents/sf10/sf10_form.html'
    success_url = reverse_lazy('documents:sf10_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'SF10 document created successfully!')
        return super().form_valid(form)

class SF10UpdateView(LoginRequiredMixin, UpdateView):
    """Update SF10 document"""
    model = SF10Document
    form_class = SF10DocumentForm
    template_name = 'documents/sf10/sf10_form.html'
    success_url = reverse_lazy('documents:sf10_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'SF10 document updated successfully!')
        return super().form_valid(form)

@login_required
def sf10_upload(request):
    """Upload SF10 Excel file"""
    if not PANDAS_AVAILABLE:
        messages.error(request, 'Excel upload functionality requires pandas. Please contact the administrator.')
        return redirect('documents:sf10_list')
    
    if request.method == 'POST':
        form = SF10UploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.created_by = request.user
            upload.status = 'processing'
            upload.save()
            
            try:
                # Process Excel file
                df = pd.read_excel(upload.excel_file)
                upload.total_records = len(df)
                upload.save()
                
                processed_count = 0
                failed_count = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        # Get or create student
                        student = None
                        if 'student_id' in row and pd.notna(row['student_id']):
                            try:
                                student = Student.objects.get(student_id=str(row['student_id']))
                            except Student.DoesNotExist:
                                pass
                        
                        if not student and 'lrn' in row and pd.notna(row['lrn']):
                            # Try to find by LRN in existing SF10 records
                            existing_sf10 = SF10Document.objects.filter(lrn=str(row['lrn'])).first()
                            if existing_sf10:
                                student = existing_sf10.student
                        
                        if not student:
                            # Create new student if not found
                            from apps.accounts.models import User
                            user = User.objects.create_user(
                                username=f"sf10_{row.get('lrn', f'student_{index}')}",
                                first_name=row.get('first_name', ''),
                                last_name=row.get('last_name', ''),
                                email=row.get('email', ''),
                            )
                            student = Student.objects.create(
                                user=user,
                                student_id=row.get('student_id', f"SF10_{index}"),
                                first_name=row.get('first_name', ''),
                                last_name=row.get('last_name', ''),
                                date_of_birth=row.get('birth_date', date.today()),
                                gender=row.get('sex', 'M'),
                                phone_number=row.get('contact_number', ''),
                            )
                        
                        # Create or update SF10 document
                        sf10_doc, created = SF10Document.objects.get_or_create(
                            student=student,
                            school_year=row.get('school_year', '2023-2024'),
                            defaults={
                                'lrn': str(row.get('lrn', '')),
                                'name': f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                                'birth_date': row.get('birth_date', date.today()),
                                'birth_place': row.get('birth_place', ''),
                                'sex': row.get('sex', 'M'),
                                'age': row.get('age', 18),
                                'present_address': row.get('present_address', ''),
                                'permanent_address': row.get('permanent_address', ''),
                                'contact_number': row.get('contact_number', ''),
                                'email': row.get('email', ''),
                                'father_name': row.get('father_name', ''),
                                'father_occupation': row.get('father_occupation', ''),
                                'father_contact': row.get('father_contact', ''),
                                'mother_name': row.get('mother_name', ''),
                                'mother_occupation': row.get('mother_occupation', ''),
                                'mother_contact': row.get('mother_contact', ''),
                                'guardian_name': row.get('guardian_name', ''),
                                'guardian_relationship': row.get('guardian_relationship', ''),
                                'guardian_contact': row.get('guardian_contact', ''),
                                'previous_school': row.get('previous_school', ''),
                                'previous_grade': row.get('previous_grade', ''),
                                'date_of_enrollment': row.get('date_of_enrollment', date.today()),
                                'date_of_graduation': row.get('date_of_graduation'),
                                'grade_level': row.get('grade_level', 'Grade 12'),
                                'section': row.get('section', ''),
                                'created_by': request.user,
                            }
                        )
                        
                        processed_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        errors.append(f"Row {index + 1}: {str(e)}")
                        continue
                
                # Update upload status
                upload.processed_records = processed_count
                upload.failed_records = failed_count
                upload.status = 'completed' if failed_count == 0 else 'failed'
                upload.completed_at = timezone.now()
                upload.error_log = '\n'.join(errors[:10])  # Limit error log
                upload.save()
                
                if failed_count == 0:
                    messages.success(request, f'Successfully processed {processed_count} SF10 records!')
                else:
                    messages.warning(request, f'Processed {processed_count} records, {failed_count} failed. Check error log.')
                
                return redirect('documents:sf10_list')
                
            except Exception as e:
                upload.status = 'failed'
                upload.error_log = str(e)
                upload.save()
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = SF10UploadForm()
    
    context = {'form': form}
    return render(request, 'documents/sf10/sf10_upload.html', context)

@login_required
def sf10_download_template(request):
    """Download SF10 Excel template"""
    if not PANDAS_AVAILABLE:
        messages.error(request, 'Excel template download requires pandas. Please contact the administrator.')
        return redirect('documents:sf10_list')
    
    # Create sample SF10 data
    sample_data = {
        'student_id': ['STU001', 'STU002'],
        'lrn': ['123456789012', '123456789013'],
        'first_name': ['John', 'Jane'],
        'last_name': ['Doe', 'Smith'],
        'birth_date': ['2005-01-15', '2005-03-20'],
        'birth_place': ['Manila', 'Quezon City'],
        'sex': ['M', 'F'],
        'age': [18, 18],
        'present_address': ['123 Main St, Manila', '456 Oak Ave, Quezon City'],
        'permanent_address': ['123 Main St, Manila', '456 Oak Ave, Quezon City'],
        'contact_number': ['09123456789', '09123456790'],
        'email': ['john.doe@email.com', 'jane.smith@email.com'],
        'father_name': ['Juan Doe', 'Pedro Smith'],
        'father_occupation': ['Engineer', 'Teacher'],
        'father_contact': ['09123456788', '09123456787'],
        'mother_name': ['Maria Doe', 'Ana Smith'],
        'mother_occupation': ['Nurse', 'Doctor'],
        'mother_contact': ['09123456787', '09123456786'],
        'guardian_name': ['Juan Doe', 'Pedro Smith'],
        'guardian_relationship': ['Father', 'Father'],
        'guardian_contact': ['09123456788', '09123456787'],
        'previous_school': ['ABC Elementary', 'XYZ High School'],
        'previous_grade': ['Grade 11', 'Grade 11'],
        'date_of_enrollment': ['2023-06-01', '2023-06-01'],
        'date_of_graduation': ['2024-03-15', '2024-03-15'],
        'school_year': ['2023-2024', '2023-2024'],
        'grade_level': ['Grade 12', 'Grade 12'],
        'section': ['Section A', 'Section B'],
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='SF10_Data', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="sf10_template.xlsx"'
    
    return response

@login_required
def sf10_statistics(request):
    """SF10 statistics and reports"""
    # Basic statistics
    total_sf10 = SF10Document.objects.count()
    active_sf10 = SF10Document.objects.filter(status='active').count()
    transferred_sf10 = SF10Document.objects.filter(status='transferred').count()
    complete_sf10 = SF10Document.objects.filter(is_complete=True).count()
    
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
        'status_stats': status_stats,
        'grade_stats': grade_stats,
        'year_stats': year_stats,
    }
    
    return render(request, 'documents/sf10/sf10_statistics.html', context)

@login_required
def sf10_dashboard(request):
    """SF10 Dashboard view"""
    # Get basic statistics
    total_documents = SF10Document.objects.count()
    recent_documents = SF10Document.objects.order_by('-created_at')[:5]
    
    context = {
        'total_documents': total_documents,
        'recent_documents': recent_documents,
    }
    
    return render(request, 'documents/sf10/dashboard.html', context)