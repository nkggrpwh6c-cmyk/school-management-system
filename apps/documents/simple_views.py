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
            document.claimed_by_id_number = form.cleaned_data['claimed_by_id_number']
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
        document.claimed_by_id_number = ''
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
    
    context = {
        'total_docs': total_docs,
        'available_docs': available_docs,
        'claimed_docs': claimed_docs,
        'lost_docs': lost_docs,
        'status_stats': status_stats,
        'type_stats': type_stats,
        'recent_claims': recent_claims,
    }
    
    return render(request, 'documents/statistics.html', context)

@login_required
def excel_import(request):
    """Import documents from Excel file - Basic version without pandas"""
    messages.info(request, 'Excel import functionality is coming soon. For now, you can add documents manually.')
    return redirect('documents:document_list')

@login_required
def download_template(request):
    """Download Excel template for import - Basic version"""
    messages.info(request, 'Excel template download is coming soon.')
    return redirect('documents:document_list')
