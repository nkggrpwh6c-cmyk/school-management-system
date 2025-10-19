"""
Security middleware for comprehensive monitoring and protection
"""
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('security')
User = get_user_model()


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive security monitoring and protection
    """
    
    def process_request(self, request):
        """Process incoming requests for security monitoring"""
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check for suspicious patterns
        self._check_suspicious_activity(request, client_ip, user_agent)
        
        # Rate limiting for sensitive endpoints
        if self._is_sensitive_endpoint(request):
            if self._is_rate_limited(client_ip):
                logger.warning(f"Rate limited request blocked from IP: {client_ip}")
                from django.http import HttpResponseTooManyRequests
                return HttpResponseTooManyRequests("Too many requests")
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing responses for security logging"""
        # Log security events
        if hasattr(request, 'security_event'):
            self._log_security_event(request, response)
        
        # Add security headers
        response = self._add_security_headers(response)
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _check_suspicious_activity(self, request, client_ip, user_agent):
        """Check for suspicious activity patterns"""
        suspicious_patterns = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'zap',
            'burp', 'w3af', 'acunetix', 'nessus', 'openvas'
        ]
        
        # Check user agent for security tools
        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if pattern in user_agent_lower:
                self._log_suspicious_activity(
                    request, client_ip, user_agent,
                    f"Suspicious user agent detected: {pattern}"
                )
                break
        
        # Check for SQL injection attempts
        if self._detect_sql_injection(request):
            self._log_suspicious_activity(
                request, client_ip, user_agent,
                "Potential SQL injection attempt detected"
            )
        
        # Check for XSS attempts
        if self._detect_xss_attempt(request):
            self._log_suspicious_activity(
                request, client_ip, user_agent,
                "Potential XSS attempt detected"
            )
    
    def _detect_sql_injection(self, request):
        """Detect potential SQL injection attempts"""
        sql_patterns = [
            'union select', 'drop table', 'delete from', 'insert into',
            'update set', 'exec(', 'execute(', 'script>', 'javascript:',
            'onload=', 'onerror=', 'onclick=', 'onmouseover='
        ]
        
        # Check GET parameters
        for key, value in request.GET.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in sql_patterns:
                    if pattern in value_lower:
                        return True
        
        # Check POST data
        if request.method == 'POST':
            for key, value in request.POST.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    for pattern in sql_patterns:
                        if pattern in value_lower:
                            return True
        
        return False
    
    def _detect_xss_attempt(self, request):
        """Detect potential XSS attempts"""
        xss_patterns = [
            '<script', 'javascript:', 'onload=', 'onerror=',
            'onclick=', 'onmouseover=', 'onfocus=', 'onblur=',
            'onchange=', 'onsubmit=', 'onreset=', 'onkeydown=',
            'onkeyup=', 'onkeypress=', 'onmousedown=', 'onmouseup='
        ]
        
        # Check GET parameters
        for key, value in request.GET.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in xss_patterns:
                    if pattern in value_lower:
                        return True
        
        # Check POST data
        if request.method == 'POST':
            for key, value in request.POST.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    for pattern in xss_patterns:
                        if pattern in value_lower:
                            return True
        
        return False
    
    def _is_sensitive_endpoint(self, request):
        """Check if the endpoint is sensitive and needs rate limiting"""
        sensitive_paths = [
            '/accounts/login/',
            '/accounts/signup/',
            '/admin/',
            '/api/',
        ]
        
        for path in sensitive_paths:
            if request.path.startswith(path):
                return True
        
        return False
    
    def _is_rate_limited(self, client_ip):
        """Check if client IP is rate limited"""
        rate_limit_key = f"rate_limit:{client_ip}"
        return cache.get(rate_limit_key) is not None
    
    def _log_suspicious_activity(self, request, client_ip, user_agent, description):
        """Log suspicious activity"""
        logger.warning(f"Suspicious activity detected: {description} from {client_ip}")
        
        # Store in database if user is authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            from .models import SecurityEvent
            SecurityEvent.objects.create(
                user=request.user,
                event_type='SUSPICIOUS_ACTIVITY',
                description=description,
                ip_address=client_ip,
                user_agent=user_agent,
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'timestamp': timezone.now().isoformat()
                }
            )
        else:
            # Log for anonymous users too
            from .models import SecurityEvent
            SecurityEvent.objects.create(
                user=None,
                event_type='SUSPICIOUS_ACTIVITY',
                description=description,
                ip_address=client_ip,
                user_agent=user_agent,
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'timestamp': timezone.now().isoformat()
                }
            )
    
    def _log_security_event(self, request, response):
        """Log security events to database"""
        if hasattr(request, 'security_event'):
            from .models import SecurityEvent
            user = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
                
            SecurityEvent.objects.create(
                user=user,
                event_type=request.security_event['type'],
                description=request.security_event['description'],
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata=request.security_event.get('metadata', {})
            )
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive audit logging
    """
    
    def process_request(self, request):
        """Log request details for audit trail"""
        # Check if user attribute exists (after AuthenticationMiddleware)
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Log sensitive operations
            if self._is_sensitive_operation(request):
                logger.info(
                    f"Audit: {request.user.username} {request.method} {request.path} "
                    f"from {self._get_client_ip(request)}"
                )
    
    def _is_sensitive_operation(self, request):
        """Check if operation is sensitive and should be logged"""
        sensitive_patterns = [
            '/admin/',
            '/accounts/',
            '/students/create/',
            '/students/edit/',
            '/grades/',
            '/fees/',
            '/reports/',
        ]
        
        for pattern in sensitive_patterns:
            if request.path.startswith(pattern):
                return True
        
        return False
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

