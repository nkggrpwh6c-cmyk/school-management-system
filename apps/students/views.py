from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Student, Attendance, StudentDocument, Grade, Section, AcademicYear
from .forms import StudentRegistrationForm, StudentUpdateForm, AttendanceForm, StudentDocumentForm, StudentSearchForm


class StudentDashboardView(LoginRequiredMixin, ListView):
    """
    Student dashboard view
    """
    model = Student
    template_name = 'students/dashboard.html'
    context_object_name = 'students'
    
    def get_queryset(self):
        if self.request.user.is_student():
            return Student.objects.filter(user=self.request.user)
        return Student.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_student():
            student = self.request.user.student_profile
            context['student'] = student
            context['recent_attendance'] = Attendance.objects.filter(
                student=student
            ).order_by('-date')[:10]
            context['attendance_stats'] = self.get_attendance_stats(student)
        return context
    
    def get_attendance_stats(self, student):
        from datetime import date, timedelta
        today = date.today()
        start_of_month = today.replace(day=1)
        
        total_days = Attendance.objects.filter(
            student=student,
            date__gte=start_of_month
        ).count()
        
        present_days = Attendance.objects.filter(
            student=student,
            date__gte=start_of_month,
            status='P'
        ).count()
        
        if total_days > 0:
            attendance_percentage = (present_days / total_days) * 100
        else:
            attendance_percentage = 0
            
        return {
            'total_days': total_days,
            'present_days': present_days,
            'attendance_percentage': round(attendance_percentage, 2)
        }


class StudentListView(LoginRequiredMixin, ListView):
    """
    Student list view with search and filters
    """
    model = Student
    template_name = 'students/student_list.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Student.objects.select_related('user', 'grade', 'section', 'academic_year')
        
        # Apply search filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(student_id__icontains=search) |
                Q(admission_number__icontains=search)
            )
        
        grade = self.request.GET.get('grade')
        if grade:
            queryset = queryset.filter(grade_id=grade)
        
        section = self.request.GET.get('section')
        if section:
            queryset = queryset.filter(section_id=section)
        
        academic_year = self.request.GET.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year_id=academic_year)
        
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'on')
        
        return queryset.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = StudentSearchForm(self.request.GET)
        context['grades'] = Grade.objects.filter(is_active=True)
        context['sections'] = Section.objects.filter(is_active=True)
        context['academic_years'] = AcademicYear.objects.all()
        return context


class StudentDetailView(LoginRequiredMixin, DetailView):
    """
    Student detail view
    """
    model = Student
    template_name = 'students/student_detail.html'
    context_object_name = 'student'
    
    def get_queryset(self):
        if self.request.user.is_student():
            return Student.objects.filter(user=self.request.user)
        return Student.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        
        # Get recent attendance
        context['recent_attendance'] = Attendance.objects.filter(
            student=student
        ).order_by('-date')[:20]
        
        # Get attendance statistics
        context['attendance_stats'] = self.get_attendance_stats(student)
        
        # Get documents
        context['documents'] = StudentDocument.objects.filter(
            student=student
        ).order_by('-uploaded_at')
        
        return context
    
    def get_attendance_stats(self, student):
        from datetime import date, timedelta
        today = date.today()
        start_of_month = today.replace(day=1)
        
        total_days = Attendance.objects.filter(
            student=student,
            date__gte=start_of_month
        ).count()
        
        present_days = Attendance.objects.filter(
            student=student,
            date__gte=start_of_month,
            status='P'
        ).count()
        
        if total_days > 0:
            attendance_percentage = (present_days / total_days) * 100
        else:
            attendance_percentage = 0
            
        return {
            'total_days': total_days,
            'present_days': present_days,
            'attendance_percentage': round(attendance_percentage, 2)
        }


class StudentCreateView(LoginRequiredMixin, CreateView):
    """
    Create new student
    """
    model = Student
    form_class = StudentRegistrationForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Student created successfully!')
        return super().form_valid(form)


class StudentProfileView(LoginRequiredMixin, DetailView):
    """
    Student profile view
    """
    model = Student
    template_name = 'students/profile.html'
    context_object_name = 'student'
    
    def get_object(self):
        if self.request.user.is_student():
            return self.request.user.student_profile
        return super().get_object()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        
        # Get recent attendance
        context['recent_attendance'] = Attendance.objects.filter(
            student=student
        ).order_by('-date')[:20]
        
        # Get attendance statistics
        context['attendance_stats'] = self.get_attendance_stats(student)
        
        # Get documents
        context['documents'] = StudentDocument.objects.filter(
            student=student
        ).order_by('-uploaded_at')
        
        return context
    
    def get_attendance_stats(self, student):
        from datetime import date, timedelta
        today = date.today()
        start_of_month = today.replace(day=1)
        
        total_days = Attendance.objects.filter(
            student=student,
            date__gte=start_of_month
        ).count()
        
        present_days = Attendance.objects.filter(
            student=student,
            date__gte=start_of_month,
            status='P'
        ).count()
        
        if total_days > 0:
            attendance_percentage = (present_days / total_days) * 100
        else:
            attendance_percentage = 0
            
        return {
            'total_days': total_days,
            'present_days': present_days,
            'attendance_percentage': round(attendance_percentage, 2)
        }


class StudentUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update student information
    """
    model = Student
    form_class = StudentUpdateForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('students:student_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Student updated successfully!')
        return super().form_valid(form)


@login_required
def mark_attendance(request):
    """
    Mark attendance for students
    """
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.marked_by = request.user
            attendance.save()
            messages.success(request, 'Attendance marked successfully!')
            return redirect('students:attendance_list')
    else:
        form = AttendanceForm()
    
    context = {
        'form': form,
        'students': Student.objects.filter(is_active=True).select_related('user', 'grade', 'section')
    }
    return render(request, 'students/mark_attendance.html', context)


@login_required
def attendance_list(request):
    """
    View attendance records
    """
    attendances = Attendance.objects.select_related(
        'student__user', 'marked_by'
    ).order_by('-date')
    
    # Apply filters
    student_id = request.GET.get('student')
    if student_id:
        attendances = attendances.filter(student_id=student_id)
    
    date_from = request.GET.get('date_from')
    if date_from:
        attendances = attendances.filter(date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        attendances = attendances.filter(date__lte=date_to)
    
    status = request.GET.get('status')
    if status:
        attendances = attendances.filter(status=status)
    
    paginator = Paginator(attendances, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'students': Student.objects.filter(is_active=True),
        'status_choices': Attendance.STATUS_CHOICES
    }
    return render(request, 'students/attendance_list.html', context)


@login_required
def upload_document(request, student_id):
    """
    Upload document for student
    """
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.student = student
            document.save()
            messages.success(request, 'Document uploaded successfully!')
            return redirect('students:student_detail', pk=student_id)
    else:
        form = StudentDocumentForm()
    
    context = {
        'form': form,
        'student': student
    }
    return render(request, 'students/upload_document.html', context)


@login_required
def student_statistics(request):
    """
    Student statistics view
    """
    stats = {
        'total_students': Student.objects.filter(is_active=True).count(),
        'students_by_grade': Student.objects.filter(is_active=True).values(
            'grade__name'
        ).annotate(count=Count('id')).order_by('grade__name'),
        'students_by_section': Student.objects.filter(is_active=True).values(
            'section__name', 'grade__name'
        ).annotate(count=Count('id')).order_by('grade__name', 'section__name'),
        'attendance_stats': Attendance.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
    }
    
    return render(request, 'students/statistics.html', {'stats': stats})
