"""
Simple Bulk Import System for Students
Basic CSV/Excel import without pandas dependency
"""
import csv
import io
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .models import Student
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SimpleStudentBulkImporter:
    """
    Simple bulk import of students from CSV files
    """
    
    # Required columns for import
    REQUIRED_COLUMNS = [
        'first_name',
        'last_name', 
        'email',
        'lrn',  # Learner Reference Number
        'grade_level',
        'section'
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.import_data = []
    
    def validate_file(self, file):
        """
        Validate the uploaded CSV file
        """
        try:
            # Check file extension
            if not file.name.lower().endswith('.csv'):
                raise ValidationError("File must be CSV format")
            
            # Read CSV file
            content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(content))
            
            # Check if file is empty
            rows = list(csv_reader)
            if not rows:
                raise ValidationError("File is empty")
            
            # Check for required columns
            missing_columns = []
            for col in self.REQUIRED_COLUMNS:
                if col not in csv_reader.fieldnames:
                    missing_columns.append(col)
            
            if missing_columns:
                raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
            
            return rows
            
        except Exception as e:
            raise ValidationError(f"Error reading file: {str(e)}")
    
    def clean_data(self, rows):
        """
        Clean and standardize the data
        """
        cleaned_rows = []
        
        for row in rows:
            # Remove empty rows
            if not any(row.values()):
                continue
                
            # Strip whitespace from string values
            cleaned_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    cleaned_row[key.strip()] = value.strip()
                else:
                    cleaned_row[key] = value
            
            cleaned_rows.append(cleaned_row)
        
        return cleaned_rows
    
    def validate_student_data(self, row_data, row_number):
        """
        Validate individual student data
        """
        errors = []
        
        # Required field validation
        if not row_data.get('first_name'):
            errors.append("First name is required")
        if not row_data.get('last_name'):
            errors.append("Last name is required")
        if not row_data.get('email'):
            errors.append("Email is required")
        if not row_data.get('lrn'):
            errors.append("LRN is required")
        if not row_data.get('grade_level'):
            errors.append("Grade level is required")
        if not row_data.get('section'):
            errors.append("Section is required")
        
        # Email validation
        if row_data.get('email') and '@' not in str(row_data['email']):
            errors.append("Invalid email format")
        
        # LRN validation (should be numeric)
        if row_data.get('lrn'):
            try:
                int(str(row_data['lrn']).replace('-', ''))
            except ValueError:
                errors.append("LRN must be numeric")
        
        # Grade level validation
        if row_data.get('grade_level'):
            try:
                grade = int(row_data['grade_level'])
                if grade < 1 or grade > 12:
                    errors.append("Grade level must be between 1 and 12")
            except ValueError:
                errors.append("Grade level must be numeric")
        
        # Check for duplicate LRN
        if row_data.get('lrn'):
            existing_student = Student.objects.filter(lrn=row_data['lrn']).first()
            if existing_student:
                errors.append(f"LRN {row_data['lrn']} already exists")
        
        # Check for duplicate email
        if row_data.get('email'):
            existing_user = User.objects.filter(email=row_data['email']).first()
            if existing_user:
                errors.append(f"Email {row_data['email']} already exists")
        
        return errors
    
    def generate_username(self, first_name, last_name, lrn):
        """
        Generate unique username for student
        """
        # Try firstname.lastname format
        base_username = f"{first_name.lower()}.{last_name.lower()}"
        username = base_username
        
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username
    
    def generate_password(self, lrn):
        """
        Generate initial password for student
        """
        # Use LRN as initial password (students can change it)
        return str(lrn)
    
    def import_students(self, file):
        """
        Main import function
        """
        try:
            # Validate file
            rows = self.validate_file(file)
            
            # Clean data
            rows = self.clean_data(rows)
            
            # Process each row
            for index, row_data in enumerate(rows):
                row_number = index + 2  # +2 because CSV is 1-indexed and has header
                
                # Validate student data
                errors = self.validate_student_data(row_data, row_number)
                
                if errors:
                    self.errors.append({
                        'row': row_number,
                        'data': row_data,
                        'errors': errors
                    })
                    continue
                
                # Add to import data
                self.import_data.append({
                    'row_number': row_number,
                    'data': row_data
                })
            
            return True
            
        except Exception as e:
            self.errors.append({
                'row': 0,
                'data': {},
                'errors': [str(e)]
            })
            return False
    
    @transaction.atomic
    def create_students(self):
        """
        Create student accounts and records
        """
        created_students = []
        
        for item in self.import_data:
            try:
                data = item['data']
                
                # Generate username and password
                username = self.generate_username(
                    data['first_name'], 
                    data['last_name'], 
                    data['lrn']
                )
                password = self.generate_password(data['lrn'])
                
                # Create user account
                user = User.objects.create_user(
                    username=username,
                    email=data['email'],
                    password=password,
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    role='STUDENT',
                    is_active=True
                )
                
                # Create student profile
                student = Student.objects.create(
                    user=user,
                    lrn=data['lrn'],
                    grade_level=data['grade_level'],
                    section=data['section'],
                    middle_name=data.get('middle_name', ''),
                    date_of_birth=data.get('date_of_birth'),
                    gender=data.get('gender', ''),
                    address=data.get('address', ''),
                    phone_number=data.get('phone_number', ''),
                    parent_name=data.get('parent_name', ''),
                    parent_phone=data.get('parent_phone', ''),
                    parent_email=data.get('parent_email', ''),
                    emergency_contact=data.get('emergency_contact', ''),
                    emergency_phone=data.get('emergency_phone', ''),
                    blood_type=data.get('blood_type', ''),
                    medical_conditions=data.get('medical_conditions', ''),
                    allergies=data.get('allergies', '')
                )
                
                created_students.append({
                    'student': student,
                    'username': username,
                    'password': password
                })
                
                self.success_count += 1
                
            except Exception as e:
                self.errors.append({
                    'row': item['row_number'],
                    'data': item['data'],
                    'errors': [f"Error creating student: {str(e)}"]
                })
        
        return created_students
    
    def get_import_summary(self):
        """
        Get summary of import results
        """
        return {
            'total_processed': len(self.import_data),
            'success_count': self.success_count,
            'error_count': len(self.errors),
            'errors': self.errors,
            'warnings': self.warnings
        }
