"""
Custom password validators for enhanced security
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexPasswordValidator:
    """
    Custom password validator that enforces complex password requirements
    """
    
    def __init__(self, min_length=12, require_uppercase=True, require_lowercase=True, 
                 require_digits=True, require_special_chars=True, max_similarity=0.7):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special_chars = require_special_chars
        self.max_similarity = max_similarity
    
    def validate(self, password, user=None):
        errors = []
        
        # Check minimum length
        if len(password) < self.min_length:
            errors.append(
                ValidationError(
                    _("Password must be at least %(min_length)d characters long."),
                    code='password_too_short',
                    params={'min_length': self.min_length},
                )
            )
        
        # Check for uppercase letters
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one uppercase letter."),
                    code='password_no_upper',
                )
            )
        
        # Check for lowercase letters
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one lowercase letter."),
                    code='password_no_lower',
                )
            )
        
        # Check for digits
        if self.require_digits and not re.search(r'\d', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one digit."),
                    code='password_no_digit',
                )
            )
        
        # Check for special characters
        if self.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."),
                    code='password_no_special',
                )
            )
        
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            errors.append(
                ValidationError(
                    _("Password cannot contain more than 2 consecutive identical characters."),
                    code='password_repeated_chars',
                )
            )
        
        # Check for sequential characters
        if self._has_sequential_chars(password):
            errors.append(
                ValidationError(
                    _("Password cannot contain sequential characters (abc, 123, etc.)."),
                    code='password_sequential',
                )
            )
        
        # Check for keyboard patterns
        if self._has_keyboard_pattern(password):
            errors.append(
                ValidationError(
                    _("Password cannot contain keyboard patterns (qwerty, asdf, etc.)."),
                    code='password_keyboard_pattern',
                )
            )
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        help_texts = [
            f"Password must be at least {self.min_length} characters long.",
        ]
        
        if self.require_uppercase:
            help_texts.append("Must contain at least one uppercase letter.")
        if self.require_lowercase:
            help_texts.append("Must contain at least one lowercase letter.")
        if self.require_digits:
            help_texts.append("Must contain at least one digit.")
        if self.require_special_chars:
            help_texts.append("Must contain at least one special character.")
        
        help_texts.extend([
            "Cannot contain more than 2 consecutive identical characters.",
            "Cannot contain sequential characters (abc, 123, etc.).",
            "Cannot contain keyboard patterns (qwerty, asdf, etc.).",
        ])
        
        return " ".join(help_texts)
    
    def _has_sequential_chars(self, password):
        """Check for sequential characters like abc, 123, etc."""
        password_lower = password.lower()
        
        # Check for alphabetic sequences
        for i in range(len(password_lower) - 2):
            if (password_lower[i:i+3].isalpha() and 
                ord(password_lower[i+1]) == ord(password_lower[i]) + 1 and
                ord(password_lower[i+2]) == ord(password_lower[i]) + 2):
                return True
        
        # Check for numeric sequences
        for i in range(len(password) - 2):
            if (password[i:i+3].isdigit() and
                int(password[i+1]) == int(password[i]) + 1 and
                int(password[i+2]) == int(password[i]) + 2):
                return True
        
        return False
    
    def _has_keyboard_pattern(self, password):
        """Check for common keyboard patterns"""
        keyboard_rows = [
            'qwertyuiop',
            'asdfghjkl',
            'zxcvbnm',
            '1234567890',
        ]
        
        password_lower = password.lower()
        
        for row in keyboard_rows:
            for i in range(len(row) - 2):
                pattern = row[i:i+3]
                if pattern in password_lower:
                    return True
        
        return False


class PasswordHistoryValidator:
    """
    Validator to prevent password reuse from recent history
    """
    
    def __init__(self, history_count=5):
        self.history_count = history_count
    
    def validate(self, password, user=None):
        if not user or not user.pk:
            return
        
        # Get recent password hashes from user's password history
        from .models import PasswordHistory
        
        recent_passwords = PasswordHistory.objects.filter(
            user=user
        ).order_by('-created_at')[:self.history_count]
        
        for password_record in recent_passwords:
            if password_record.check_password(password):
                raise ValidationError(
                    _("You cannot reuse any of your last %(count)d passwords."),
                    code='password_reused',
                    params={'count': self.history_count},
                )
    
    def get_help_text(self):
        return f"Cannot reuse any of your last {self.history_count} passwords."

