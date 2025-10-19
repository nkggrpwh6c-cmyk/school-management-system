from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
import secrets
import pyotp


class User(AbstractUser):
    """
    Custom User model with role-based authentication
    """
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
        ('ADMIN', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        blank=True,
        null=True
    )
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def is_student(self):
        return self.role == 'STUDENT'
    
    def is_teacher(self):
        return self.role == 'TEACHER'
    
    def is_parent(self):
        return self.role == 'PARENT'
    
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_teacher_admin(self):
        """Check if user is teacher with admin privileges for grades"""
        return self.role == 'TEACHER' and self.is_staff


class PasswordHistory(models.Model):
    """
    Store password history to prevent reuse
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_history')
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Password History"
    
    def check_password(self, raw_password):
        """Check if the provided password matches this historical password"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password_hash)


class LoginAttempt(models.Model):
    """
    Track login attempts for security monitoring
    """
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        status = "SUCCESS" if self.success else f"FAILED ({self.failure_reason})"
        return f"{self.username} from {self.ip_address} - {status}"


class SecurityEvent(models.Model):
    """
    Log security-related events
    """
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('PASSWORD_CHANGED', 'Password Changed'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('ADMIN_ACTION', 'Admin Action'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.timestamp}"


class TwoFactorAuth(models.Model):
    """
    Two-Factor Authentication settings for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    def generate_secret_key(self):
        """Generate a new secret key for TOTP"""
        self.secret_key = pyotp.random_base32()
        self.save()
        return self.secret_key
    
    def generate_backup_codes(self, count=10):
        """Generate backup codes for 2FA"""
        codes = [secrets.token_hex(4).upper() for _ in range(count)]
        self.backup_codes = codes
        self.save()
        return codes
    
    def verify_totp(self, token):
        """Verify TOTP token"""
        if not self.is_enabled or not self.secret_key:
            return False
        
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token, valid_window=1)
    
    def verify_backup_code(self, code):
        """Verify backup code"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True
        return False
    
    def get_qr_code_url(self):
        """Get QR code URL for TOTP setup"""
        if not self.secret_key:
            return None
        
        totp = pyotp.TOTP(self.secret_key)
        return totp.provisioning_uri(
            name=self.user.email or self.user.username,
            issuer_name="School Management System"
        )


class UserProfile(models.Model):
    """
    Extended profile information for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(max_length=15, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} Profile"
