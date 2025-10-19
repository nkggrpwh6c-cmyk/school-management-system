"""
Registrar-specific URLs for comprehensive student management
"""
from django.urls import path
from . import registrar_views
from . import sf10_registrar_views
from . import enhanced_registrar_views

app_name = 'registrar'

urlpatterns = [
    # Registrar Dashboard (Enhanced)
    path('', enhanced_registrar_views.enhanced_registrar_dashboard, name='registrar_dashboard'),
    
    # Student Management
    path('search/', registrar_views.student_search, name='student_search'),
    path('students/<str:student_id>/', registrar_views.student_detail, name='student_detail'),
    path('students/<str:student_id>/edit/', registrar_views.student_edit, name='student_edit'),
    
    # Document Management
    path('students/<str:student_id>/documents/upload/', registrar_views.document_upload, name='document_upload'),
    
    # Bulk Import for Registrar
    path('bulk-import/', registrar_views.bulk_import_registrar, name='bulk_import_registrar'),
    path('bulk-import/preview/', registrar_views.bulk_import_preview_registrar, name='bulk_import_preview_registrar'),
    
    # Export and Analytics
    path('export/', registrar_views.export_students, name='export_students'),
    path('analytics/', registrar_views.student_analytics, name='student_analytics'),
    
    # SF10 Document Management
    path('sf10/', sf10_registrar_views.sf10_dashboard, name='sf10_dashboard'),
    path('sf10/list/', sf10_registrar_views.sf10_list, name='sf10_list'),
    path('sf10/create/', sf10_registrar_views.sf10_create, name='sf10_create'),
    path('sf10/<int:pk>/', sf10_registrar_views.sf10_detail, name='sf10_detail'),
    path('sf10/<int:pk>/edit/', sf10_registrar_views.sf10_edit, name='sf10_edit'),
    path('sf10/upload/', sf10_registrar_views.sf10_upload, name='sf10_upload'),
    path('sf10/template/', sf10_registrar_views.sf10_download_template, name='sf10_download_template'),
    path('sf10/statistics/', sf10_registrar_views.sf10_statistics, name='sf10_statistics'),
    
    # Enhanced Features (now integrated into main dashboard)
    path('validation/', enhanced_registrar_views.smart_student_validation, name='smart_validation'),
    path('archive/<str:student_id>/', enhanced_registrar_views.archive_student, name='archive_student'),
    path('restore/<str:student_id>/', enhanced_registrar_views.restore_student, name='restore_student'),
    path('bulk-archive/', enhanced_registrar_views.bulk_archive_students, name='bulk_archive'),
    path('backup/', enhanced_registrar_views.create_backup, name='create_backup'),
    path('health-check/', enhanced_registrar_views.system_health_check, name='health_check'),
    path('auto-archive/', enhanced_registrar_views.auto_archive_inactive, name='auto_archive'),
    path('cleanup/', enhanced_registrar_views.cleanup_old_archives, name='cleanup_archives'),
]
