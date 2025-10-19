"""
Custom authentication backends with security features
"""
import time
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('security')

User = get_user_model()


class RateLimitedModelBackend(ModelBackend):
    """
    Authentication backend with rate limiting and account lockout protection
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        # Check if account is locked
        if self._is_account_locked(username):
            logger.warning(f"Login attempt blocked - account locked: {username}")
            return None
        
        # Attempt authentication
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user is not None:
            # Successful login - reset failed attempts
            self._reset_failed_attempts(username)
            logger.info(f"Successful login: {username}")
            return user
        else:
            # Failed login - increment failed attempts
            self._record_failed_attempt(username, request)
            logger.warning(f"Failed login attempt: {username}")
            return None
    
    def _is_account_locked(self, username):
        """Check if account is locked due to too many failed attempts"""
        lockout_key = f"account_lockout:{username}"
        return cache.get(lockout_key) is not None
    
    def _record_failed_attempt(self, username, request):
        """Record a failed login attempt"""
        attempts_key = f"login_attempts:{username}"
        current_attempts = cache.get(attempts_key, 0)
        new_attempts = current_attempts + 1
        
        # Set timeout for attempts counter
        timeout = getattr(settings, 'LOGIN_ATTEMPTS_TIMEOUT', 300)
        cache.set(attempts_key, new_attempts, timeout)
        
        # Check if account should be locked
        max_attempts = getattr(settings, 'LOGIN_ATTEMPTS_LIMIT', 5)
        if new_attempts >= max_attempts:
            self._lock_account(username)
            logger.warning(f"Account locked due to too many failed attempts: {username}")
    
    def _lock_account(self, username):
        """Lock account for specified duration"""
        lockout_key = f"account_lockout:{username}"
        lockout_duration = getattr(settings, 'ACCOUNT_LOCKOUT_DURATION', 1800)
        cache.set(lockout_key, True, lockout_duration)
        
        # Log security event
        logger.warning(f"Account locked: {username} for {lockout_duration} seconds")
    
    def _reset_failed_attempts(self, username):
        """Reset failed attempts counter on successful login"""
        attempts_key = f"login_attempts:{username}"
        lockout_key = f"account_lockout:{username}"
        cache.delete(attempts_key)
        cache.delete(lockout_key)


class IPRateLimitedBackend(RateLimitedModelBackend):
    """
    Authentication backend with IP-based rate limiting
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is None:
            return None
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check IP-based rate limiting
        if self._is_ip_rate_limited(client_ip):
            logger.warning(f"Login attempt blocked - IP rate limited: {client_ip}")
            return None
        
        # Proceed with normal authentication
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user is None:
            # Record failed attempt for IP
            self._record_ip_failed_attempt(client_ip)
        
        return user
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_ip_rate_limited(self, ip):
        """Check if IP is rate limited"""
        ip_key = f"ip_rate_limit:{ip}"
        return cache.get(ip_key) is not None
    
    def _record_ip_failed_attempt(self, ip):
        """Record failed attempt for IP"""
        ip_attempts_key = f"ip_attempts:{ip}"
        current_attempts = cache.get(ip_attempts_key, 0)
        new_attempts = current_attempts + 1
        
        # Set timeout for IP attempts counter
        timeout = getattr(settings, 'LOGIN_ATTEMPTS_TIMEOUT', 300)
        cache.set(ip_attempts_key, new_attempts, timeout)
        
        # Check if IP should be rate limited
        max_attempts = getattr(settings, 'LOGIN_ATTEMPTS_LIMIT', 5)
        if new_attempts >= max_attempts:
            self._rate_limit_ip(ip)
            logger.warning(f"IP rate limited due to too many failed attempts: {ip}")
    
    def _rate_limit_ip(self, ip):
        """Rate limit IP for specified duration"""
        ip_key = f"ip_rate_limit:{ip}"
        rate_limit_duration = getattr(settings, 'ACCOUNT_LOCKOUT_DURATION', 1800)
        cache.set(ip_key, True, rate_limit_duration)
        
        # Log security event
        logger.warning(f"IP rate limited: {ip} for {rate_limit_duration} seconds")

