"""
Smart Data Validation System for Student Records
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from datetime import date, datetime
import re
from .models import Student
from apps.documents.sf10_models import SF10Document

class SmartDataValidator:
    """Comprehensive data validation for student records"""
    
    @staticmethod
    def validate_lrn(lrn, student_id=None):
        """Validate LRN (Learner Reference Number)"""
        if not lrn:
            raise ValidationError("LRN is required")
        
        # Check LRN format (12 digits)
        if not re.match(r'^\d{12}$', lrn):
            raise ValidationError("LRN must be exactly 12 digits")
        
        # Check SF10 documents for LRN duplicates
        existing_sf10 = SF10Document.objects.filter(lrn=lrn).exclude(student__student_id=student_id).first()
        if existing_sf10:
            raise ValidationError(f"LRN {lrn} already exists in SF10 document for {existing_sf10.name}")
        
        return True
    
    @staticmethod
    def validate_birth_date(birth_date):
        """Validate birth date"""
        if not birth_date:
            raise ValidationError("Birth date is required")
        
        # Convert string to date if needed
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                try:
                    birth_date = datetime.strptime(birth_date, '%m/%d/%Y').date()
                except ValueError:
                    raise ValidationError("Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY")
        
        # Check if birth date is not in the future
        if birth_date > date.today():
            raise ValidationError("Birth date cannot be in the future")
        
        # Check if student is not too old (e.g., 100 years)
        age = (date.today() - birth_date).days // 365
        if age > 100:
            raise ValidationError("Student age seems unrealistic (over 100 years)")
        
        # Check if student is not too young (e.g., under 3 years)
        if age < 3:
            raise ValidationError("Student age seems unrealistic (under 3 years)")
        
        return True
    
    @staticmethod
    def validate_contact_number(contact_number):
        """Validate contact number format"""
        if not contact_number:
            return True  # Optional field
        
        # Remove spaces and special characters
        clean_number = re.sub(r'[^\d]', '', contact_number)
        
        # Check if it's a valid Philippine mobile number
        if len(clean_number) == 11 and clean_number.startswith('09'):
            return True
        elif len(clean_number) == 10 and clean_number.startswith('9'):
            return True
        else:
            raise ValidationError("Invalid contact number format. Use format: 09XX-XXX-XXXX")
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return True  # Optional field
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")
        
        return True
    
    @staticmethod
    def validate_guardian_contact(guardian_name, guardian_contact):
        """Validate guardian contact if guardian name is provided"""
        if guardian_name and not guardian_contact:
            raise ValidationError("Guardian contact number is required when guardian name is provided")
        
        if guardian_contact:
            return SmartDataValidator.validate_contact_number(guardian_contact)
        
        return True
    
    @staticmethod
    def validate_parent_contacts(father_name, father_contact, mother_name, mother_contact):
        """Validate parent contact numbers"""
        if father_name and not father_contact:
            raise ValidationError("Father's contact number is required when father's name is provided")
        
        if mother_name and not mother_contact:
            raise ValidationError("Mother's contact number is required when mother's name is provided")
        
        if father_contact:
            SmartDataValidator.validate_contact_number(father_contact)
        
        if mother_contact:
            SmartDataValidator.validate_contact_number(mother_contact)
        
        return True
    
    @staticmethod
    def validate_school_year(school_year):
        """Validate school year format"""
        if not school_year:
            raise ValidationError("School year is required")
        
        # Check format YYYY-YYYY
        if not re.match(r'^\d{4}-\d{4}$', school_year):
            raise ValidationError("School year must be in format YYYY-YYYY (e.g., 2023-2024)")
        
        # Extract years
        start_year, end_year = school_year.split('-')
        start_year, end_year = int(start_year), int(end_year)
        
        # Check if end year is start year + 1
        if end_year != start_year + 1:
            raise ValidationError("School year end year must be start year + 1")
        
        # Check if school year is not too far in the past or future
        current_year = date.today().year
        if start_year < current_year - 10:
            raise ValidationError("School year is too far in the past")
        if start_year > current_year + 2:
            raise ValidationError("School year is too far in the future")
        
        return True
    
    @staticmethod
    def validate_enrollment_dates(date_of_enrollment, date_of_graduation=None):
        """Validate enrollment and graduation dates"""
        if not date_of_enrollment:
            raise ValidationError("Date of enrollment is required")
        
        # Check if enrollment date is not in the future
        if date_of_enrollment > date.today():
            raise ValidationError("Date of enrollment cannot be in the future")
        
        # Check if enrollment date is not too far in the past
        years_ago = (date.today() - date_of_enrollment).days // 365
        if years_ago > 20:
            raise ValidationError("Date of enrollment is too far in the past")
        
        if date_of_graduation:
            # Check if graduation date is after enrollment date
            if date_of_graduation <= date_of_enrollment:
                raise ValidationError("Date of graduation must be after date of enrollment")
            
            # Check if graduation date is not in the future
            if date_of_graduation > date.today():
                raise ValidationError("Date of graduation cannot be in the future")
        
        return True
    
    @staticmethod
    def validate_student_data(data):
        """Comprehensive validation of student data"""
        errors = []
        warnings = []
        
        try:
            # Validate LRN
            SmartDataValidator.validate_lrn(data.get('lrn'), data.get('student_id'))
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate birth date
            if data.get('birth_date'):
                SmartDataValidator.validate_birth_date(data['birth_date'])
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate contact number
            SmartDataValidator.validate_contact_number(data.get('contact_number'))
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate email
            SmartDataValidator.validate_email(data.get('email'))
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate guardian contact
            SmartDataValidator.validate_guardian_contact(
                data.get('guardian_name'), 
                data.get('guardian_contact')
            )
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate parent contacts
            SmartDataValidator.validate_parent_contacts(
                data.get('father_name'), data.get('father_contact'),
                data.get('mother_name'), data.get('mother_contact')
            )
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate school year
            SmartDataValidator.validate_school_year(data.get('school_year'))
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            # Validate enrollment dates
            SmartDataValidator.validate_enrollment_dates(
                data.get('date_of_enrollment'),
                data.get('date_of_graduation')
            )
        except ValidationError as e:
            errors.append(str(e))
        
        # Additional warnings
        if not data.get('guardian_name') and not data.get('father_name') and not data.get('mother_name'):
            warnings.append("No parent or guardian information provided")
        
        if not data.get('contact_number') and not data.get('email'):
            warnings.append("No contact information provided")
        
        if data.get('age') and data.get('birth_date'):
            calculated_age = (date.today() - data['birth_date']).days // 365
            if abs(calculated_age - data['age']) > 1:
                warnings.append(f"Age ({data['age']}) doesn't match birth date (calculated: {calculated_age})")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

class DuplicateChecker:
    """Check for duplicate records across the system"""
    
    @staticmethod
    def check_duplicate_student(data, exclude_id=None):
        """Check for duplicate student records"""
        duplicates = []
        
        # Check by LRN in SF10 documents
        if data.get('lrn'):
            existing = SF10Document.objects.filter(lrn=data['lrn']).exclude(student__student_id=exclude_id).first()
            if existing:
                duplicates.append(f"LRN {data['lrn']} already exists in SF10 document for {existing.name}")
        
        # Check by email
        if data.get('email'):
            existing = Student.objects.filter(user__email=data['email']).exclude(student_id=exclude_id).first()
            if existing:
                duplicates.append(f"Email {data['email']} already exists for {existing.user.get_full_name()}")
        
        # Check by contact number
        if data.get('contact_number'):
            existing = Student.objects.filter(contact_number=data['contact_number']).exclude(student_id=exclude_id).first()
            if existing:
                duplicates.append(f"Contact number {data['contact_number']} already exists for {existing.user.get_full_name()}")
        
        return duplicates

class DataIntegrityChecker:
    """Check data integrity across related records"""
    
    @staticmethod
    def check_sf10_consistency(student_id):
        """Check consistency between Student and SF10 records"""
        issues = []
        
        try:
            student = Student.objects.get(student_id=student_id)
            sf10_records = SF10Document.objects.filter(student=student)
            
            for sf10 in sf10_records:
                # Check LRN consistency
                if sf10.lrn != student.lrn:
                    issues.append(f"LRN mismatch: Student LRN ({student.lrn}) vs SF10 LRN ({sf10.lrn})")
                
                # Check name consistency
                if sf10.name != student.user.get_full_name():
                    issues.append(f"Name mismatch: Student name ({student.user.get_full_name()}) vs SF10 name ({sf10.name})")
                
                # Check grade level consistency
                if hasattr(student, 'grade') and student.grade and sf10.grade_level != student.grade.name:
                    issues.append(f"Grade level mismatch: Student grade ({student.grade.name}) vs SF10 grade ({sf10.grade_level})")
        
        except Student.DoesNotExist:
            issues.append("Student record not found")
        
        return issues
