from django.urls import path
from . import views, bulk_views

app_name = 'students'

urlpatterns = [
    path('', views.StudentDashboardView.as_view(), name='dashboard'),
    path('profile/', views.StudentProfileView.as_view(), name='profile'),
    path('list/', views.StudentListView.as_view(), name='student_list'),
    path('create/', views.StudentCreateView.as_view(), name='student_create'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
    path('<int:pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('<int:student_id>/documents/upload/', views.upload_document, name='upload_document'),
    path('statistics/', views.student_statistics, name='statistics'),
    
    # Bulk Import URLs
    path('bulk-import/', bulk_views.bulk_import_dashboard, name='bulk_import_dashboard'),
    path('bulk-import/upload/', bulk_views.bulk_import_upload, name='bulk_import_upload'),
    path('bulk-import/preview/', bulk_views.bulk_import_preview, name='bulk_import_preview'),
    path('bulk-import/success/<int:success_count>/', bulk_views.bulk_import_success, name='bulk_import_success'),
    path('bulk-import/template/', bulk_views.download_template, name='download_template'),
    path('bulk-import/history/', bulk_views.bulk_import_history, name='bulk_import_history'),
]
