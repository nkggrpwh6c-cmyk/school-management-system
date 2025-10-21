"""
Comprehensive Logging Middleware for System Activity Tracking
"""
from django.utils import timezone
from .models import SecurityEvent, LoginAttempt
import json


class ComprehensiveLoggingMiddleware:
    """
    Log all system activities including:
    - User actions
    - Data changes
    - Failed attempts
    - Security events
    - Backend changes
    - Frontend interactions
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log request start
        start_time = timezone.now()
        
        # Get client info
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Process request
        response = self.get_response(request)
        
        # Log based on response status and user actions
        if request.user.is_authenticated:
            self.log_user_activity(request, response, ip_address, user_agent, start_time)
        
        # Log security events
        if response.status_code in [403, 404, 500]:
            self.log_security_event(request, response, ip_address, user_agent)
        
        return response
    
    def get_client_ip(self, request):
        """Get real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def log_user_activity(self, request, response, ip_address, user_agent, start_time):
        """Log user activities"""
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            # Log data modification attempts
            event_type = 'ADMIN_ACTION' if request.user.is_superuser else 'USER_ACTION'
            
            description = f"{request.user.username} performed {request.method} on {request.path}"
            
            # Get request data (sanitized)
            request_data = {}
            if request.method == 'POST':
                request_data = {k: v for k, v in request.POST.items() if k not in ['password', 'csrfmiddlewaretoken']}
            
            SecurityEvent.objects.create(
                user=request.user,
                event_type=event_type,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'request_data': request_data,
                    'duration_ms': int((timezone.now() - start_time).total_seconds() * 1000)
                }
            )
    
    def log_security_event(self, request, response, ip_address, user_agent):
        """Log security-related events"""
        if response.status_code == 403:
            event_type = 'SUSPICIOUS_ACTIVITY'
            description = f"403 Forbidden access attempt to {request.path}"
        elif response.status_code == 404:
            event_type = 'SUSPICIOUS_ACTIVITY'
            description = f"404 Not Found: {request.path}"
        elif response.status_code == 500:
            event_type = 'ADMIN_ACTION'
            description = f"500 Server Error on {request.path}"
        else:
            return
        
        SecurityEvent.objects.create(
            user=request.user if request.user.is_authenticated else None,
            event_type=event_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'status_code': response.status_code,
                'path': request.path,
                'method': request.method
            }
        )
