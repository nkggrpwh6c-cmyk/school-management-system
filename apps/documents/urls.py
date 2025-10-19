from django.urls import path
from . import simple_views as views
from . import sf10_views

app_name = 'documents'

urlpatterns = [
    # Dashboard and main views
    path('', views.DocumentDashboardView.as_view(), name='dashboard'),
    path('list/', views.DocumentListView.as_view(), name='document_list'),
    path('statistics/', views.document_statistics, name='statistics'),
    
    # Document CRUD
    path('create/', views.DocumentCreateView.as_view(), name='document_create'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('<int:pk>/edit/', views.DocumentUpdateView.as_view(), name='document_edit'),
    
    # Document actions
    path('<int:pk>/claim/', views.claim_document, name='claim_document'),
    path('<int:pk>/unclaim/', views.unclaim_document, name='unclaim_document'),
    
    # Import/Export
    path('import/', views.excel_import, name='excel_import'),
    path('template/', views.download_template, name='download_template'),
    
    # SF10 URLs
    path('sf10/', sf10_views.SF10DashboardView.as_view(), name='sf10_dashboard'),
    path('sf10/list/', sf10_views.SF10ListView.as_view(), name='sf10_list'),
    path('sf10/create/', sf10_views.SF10CreateView.as_view(), name='sf10_create'),
    path('sf10/<int:pk>/', sf10_views.SF10DetailView.as_view(), name='sf10_detail'),
    path('sf10/<int:pk>/edit/', sf10_views.SF10UpdateView.as_view(), name='sf10_edit'),
    path('sf10/upload/', sf10_views.sf10_upload, name='sf10_upload'),
    path('sf10/template/', sf10_views.sf10_download_template, name='sf10_download_template'),
    path('sf10/statistics/', sf10_views.sf10_statistics, name='sf10_statistics'),
]
