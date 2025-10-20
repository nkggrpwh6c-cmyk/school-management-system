"""
URL configuration for school management system.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import JsonResponse

def home_redirect(request):
    """Redirect to appropriate dashboard based on user role"""
    if request.user.is_authenticated:
        if request.user.is_student():
            return redirect('students:dashboard')
        elif request.user.is_teacher():
            return redirect('teachers:dashboard')
        elif request.user.is_parent():
            return redirect('parents:dashboard')
        elif request.user.is_admin():
            return redirect('/admin/')
    return redirect('accounts:login')

def health_check(request):
    """Health check endpoint for Render deployment"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'Application is running'
    }, status=200)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('healthz/', health_check, name='health_check'),
    path('accounts/', include('apps.accounts.urls')),
    path('students/', include('apps.students.urls')),
    path('registrar/', include('apps.students.registrar_urls')),
    path('teachers/', include('apps.teachers.urls')),
    path('parents/', include('apps.parents.urls')),
    path('fees/', include('apps.fees.urls')),
    path('timetable/', include('apps.timetable.urls')),
    path('grades/', include('apps.grades.urls')),
    path('reports/', include('apps.reports.urls')),
    path('documents/', include('apps.documents.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
