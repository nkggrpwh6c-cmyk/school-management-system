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
except ImportError:
    PANDAS_AVAILABLE = False

from .models import DocumentCategory, DocumentType, StudentDocument, DocumentClaim, DocumentBatch
from .forms import (
    DocumentCategoryForm, DocumentTypeForm, StudentDocumentForm, 
    DocumentClaimForm, DocumentSearchForm, ExcelImportForm
)
from apps.students.models import Student

class DocumentDashboardView(LoginRequiredMixin, ListView):
    """Document management dashboard for staff"""
    model = StudentDocument
    template_name = 'documents/dashboard.html'
    context_object_name = 'documents'
    paginate_by = 20
    
    def get_queryset(self):
        return StudentDocument.objects.select_related(
            'student__user', 'document_type', 'created_by'
        ).order_by('-date_created')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics
        total_docs = StudentDocument.objects.count()
        available_docs = StudentDocument.objects.filter(status='available').count()
        claimed_docs = StudentDocument.objects.filter(status='claimed').count()
        
        # Recent documents
        recent_docs = StudentDocument.objects.select_related(
            'student__user', 'document_type'
        ).order_by('-date_created')[:10]
        
        # Status distribution
        status_stats = StudentDocument.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        context.update({
            'total_docs': total_docs,
            'available_docs': available_docs,
            'claimed_docs': claimed_docs,
            'recent_docs': recent_docs,
            'status_stats': status_stats,
        })
        
        return context

class DocumentListView(LoginRequiredMixin, ListView):
    """List all documents with search and filters"""
    model = StudentDocument
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = StudentDocument.objects.select_related(
            'student__user', 'document_type', 'created_by'
        ).order_by('-date_created')
        
        # Apply search filters
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(student__user__first_name__icontains=search) |
                Q(student__user__last_name__icontains=search) |
                Q(title__icontains=search) |
                Q(document_number__icontains=search)
            )
        
        student_id = self.request.GET.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        document_type_id = self.request.GET.get('document_type')
        if document_type_id:
            queryset = queryset.filter(document_type_id=document_type_id)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date_created__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date_created__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DocumentSearchForm(self.request.GET)
        context['students'] = Student.objects.filter(is_active=True)
        context['document_types'] = DocumentType.objects.filter(is_active=True)
        return context

class DocumentDetailView(LoginRequiredMixin, DetailView):
    """View document details"""
    model = StudentDocument
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.get_object()
        context['claims'] = document.claims.all().order_by('-claim_date')
        return context

class DocumentCreateView(LoginRequiredMixin, CreateView):
    """Create new document"""
    model = StudentDocument
    form_class = StudentDocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:document_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Document created successfully!')
        return super().form_valid(form)

class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    """Update document"""
    model = StudentDocument
    form_class = StudentDocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:document_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Document updated successfully!')
        return super().form_valid(form)

@login_required
def claim_document(request, pk):
    """Claim a document"""
    document = get_object_or_404(StudentDocument, pk=pk)
    
    if document.status != 'available':
        messages.error(request, 'This document is not available for claiming.')
        return redirect('documents:document_detail', pk=pk)
    
    if request.method == 'POST':
        form = DocumentClaimForm(request.POST)
        if form.is_valid():
            # Create claim record
            claim = form.save(commit=False)
            claim.document = document
            claim.claimed_by = request.user
            claim.save()
            
            # Update document status
            document.status = 'claimed'
            document.date_claimed = timezone.now().date()
            document.claimed_by = request.user
            document.claimed_by_name = form.cleaned_data['claimed_by_name']
            document.claimed_by_relation = form.cleaned_data['claimed_by_relation']
            document.claimed_by_id = form.cleaned_data['claimed_by_id']
            document.claim_remarks = form.cleaned_data['remarks']
            document.save()
            
            messages.success(request, f'Document "{document.title}" has been claimed successfully!')
            return redirect('documents:document_detail', pk=pk)
    else:
        form = DocumentClaimForm()
    
    context = {
        'document': document,
        'form': form,
    }
    return render(request, 'documents/claim_document.html', context)

@login_required
def unclaim_document(request, pk):
    """Unclaim a document (make it available again)"""
    document = get_object_or_404(StudentDocument, pk=pk)
    
    if document.status != 'claimed':
        messages.error(request, 'This document is not claimed.')
        return redirect('documents:document_detail', pk=pk)
    
    if request.method == 'POST':
        document.status = 'available'
        document.date_claimed = None
        document.claimed_by = None
        document.claimed_by_name = ''
        document.claimed_by_relation = ''
        document.claimed_by_id = ''
        document.claim_remarks = ''
        document.save()
        
        messages.success(request, f'Document "{document.title}" has been made available again.')
        return redirect('documents:document_detail', pk=pk)
    
    context = {'document': document}
    return render(request, 'documents/unclaim_document.html', context)

@login_required
def document_statistics(request):
    """Document statistics and reports"""
    # Basic statistics
    total_docs = StudentDocument.objects.count()
    available_docs = StudentDocument.objects.filter(status='available').count()
    claimed_docs = StudentDocument.objects.filter(status='claimed').count()
    lost_docs = StudentDocument.objects.filter(status='lost').count()
    
    # Status distribution
    status_stats = StudentDocument.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    # Documents by type
    type_stats = StudentDocument.objects.values('document_type__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent claims
    recent_claims = DocumentClaim.objects.select_related(
        'document__student__user'
    ).order_by('-claim_date')[:10]
    
    # Monthly statistics
    from datetime import datetime, timedelta
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_stats = StudentDocument.objects.filter(
        date_created__gte=six_months_ago
    ).extra(
        select={'month': "DATE_TRUNC('month', date_created)"}
    ).values('month').annotate(
        created=Count('id', filter=Q(status='available')),
        claimed=Count('id', filter=Q(status='claimed'))
    ).order_by('month')
    
    context = {
        'total_docs': total_docs,
        'available_docs': available_docs,
        'claimed_docs': claimed_docs,
        'lost_docs': lost_docs,
        'status_stats': status_stats,
        'type_stats': type_stats,
        'recent_claims': recent_claims,
        'monthly_stats': monthly_stats,
    }
    
    return render(request, 'documents/statistics.html', context)

@login_required
def excel_import(request):
    """Import documents from Excel file"""
    if not PANDAS_AVAILABLE:
        messages.error(request, 'Excel import functionality requires pandas. Please contact the administrator.')
        return redirect('documents:document_list')
    
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data['excel_file']
            batch_name = form.cleaned_data['batch_name']
            description = form.cleaned_data['description']
            
            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                
                # Create batch record
                batch = DocumentBatch.objects.create(
                    name=batch_name,
                    description=description,
                    excel_file=excel_file,
                    total_documents=len(df),
                    created_by=request.user
                )
                
                # Process each row
                imported_count = 0
                failed_count = 0
                
                for index, row in df.iterrows():
                    try:
                        # Get student by student_id or name
                        student = None
                        if 'student_id' in row and pd.notna(row['student_id']):
                            student = Student.objects.get(student_id=str(row['student_id']))
                        elif 'student_name' in row and pd.notna(row['student_name']):
                            # Try to find by name
                            name_parts = str(row['student_name']).split()
                            if len(name_parts) >= 2:
                                student = Student.objects.filter(
                                    user__first_name__icontains=name_parts[0],
                                    user__last_name__icontains=name_parts[-1]
                                ).first()
                        
                        if not student:
                            failed_count += 1
                            continue
                        
                        # Get document type
                        doc_type = None
                        if 'document_type' in row and pd.notna(row['document_type']):
                            doc_type = DocumentType.objects.filter(
                                name__icontains=str(row['document_type'])
                            ).first()
                        
                        if not doc_type:
                            failed_count += 1
                            continue
                        
                        # Create document
                        document = StudentDocument.objects.create(
                            student=student,
                            document_type=doc_type,
                            title=row.get('title', f"{doc_type.name} - {student.full_name}"),
                            description=row.get('description', ''),
                            document_number=row.get('document_number', f"{doc_type.name}-{student.student_id}-{index+1}"),
                            date_issued=row.get('date_issued', date.today()) if pd.notna(row.get('date_issued')) else date.today(),
                            created_by=request.user,
                            notes=row.get('notes', '')
                        )
                        
                        imported_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        continue
                
                # Update batch
                batch.imported_documents = imported_count
                batch.failed_imports = failed_count
                batch.is_completed = True
                batch.save()
                
                messages.success(
                    request, 
                    f'Import completed! {imported_count} documents imported, {failed_count} failed.'
                )
                return redirect('documents:document_list')
                
            except Exception as e:
                messages.error(request, f'Error importing file: {str(e)}')
    else:
        form = ExcelImportForm()
    
    context = {'form': form}
    return render(request, 'documents/excel_import.html', context)

@login_required
def download_template(request):
    """Download Excel template for import"""
    if not PANDAS_AVAILABLE:
        messages.error(request, 'Excel template download requires pandas. Please contact the administrator.')
        return redirect('documents:document_list')
    
    # Create a sample Excel file
    sample_data = {
        'student_id': ['STU001', 'STU002'],
        'student_name': ['John Doe', 'Jane Smith'],
        'document_type': ['Certificate', 'Transcript'],
        'title': ['Graduation Certificate', 'Academic Transcript'],
        'description': ['High School Graduation', 'Complete Academic Record'],
        'document_number': ['CERT-001', 'TRANS-001'],
        'date_issued': ['2024-01-15', '2024-01-15'],
        'notes': ['Sample note', 'Sample note']
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Documents', index=False)
    
    output.seek(0)
    
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="document_import_template.xlsx"'
    
    return response
