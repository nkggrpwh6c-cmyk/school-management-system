from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, security_views, security_admin_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Security URLs
    path('security/', security_views.security_dashboard, name='security_dashboard'),
    path('security/events/', security_views.security_events, name='security_events'),
    path('security/attempts/', security_views.login_attempts, name='login_attempts'),
    path('security/analytics/', security_views.security_analytics, name='security_analytics'),
    path('security/settings/', security_views.security_settings, name='security_settings'),
    path('security/2fa/enable/', security_views.enable_2fa, name='enable_2fa'),
    path('security/2fa/verify/', security_views.verify_2fa_setup, name='verify_2fa_setup'),
    path('security/2fa/disable/', security_views.disable_2fa, name='disable_2fa'),
    
    # Security Admin URLs (Dedicated Security Admin Interface)
    path('security-admin/login/', security_admin_views.security_admin_login, name='security_admin_login'),
    path('security-admin/', security_admin_views.security_admin_dashboard, name='security_admin_dashboard'),
    path('security-admin/login-attempts/', security_admin_views.security_login_attempts, name='security_login_attempts'),
    path('security-admin/events/', security_admin_views.security_events_admin, name='security_events_admin'),
    path('security-admin/users/', security_admin_views.security_user_management, name='security_user_management'),
    path('security-admin/analytics/', security_admin_views.security_analytics_admin, name='security_analytics_admin'),
]
