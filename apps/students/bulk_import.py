"""
Bulk Import System for Students
Handles Excel/CSV file uploads and automatic student registration
"""
try:
    import pandas as pd
    import io
except ImportError:
    pd = None
    io = None
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from .models import Student
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class StudentBulkImporter:
    """
    Handles bulk import of students from Excel/CSV files
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
    
    # Optional columns
    OPTIONAL_COLUMNS = [
        'middle_name',
        'date_of_birth',
        'gender',
        'address',
        'phone_number',
        'parent_name',
        'parent_phone',
        'parent_email',
        'emergency_contact',
        'emergency_phone',
        'blood_type',
        'medical_conditions',
        'allergies'
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.import_data = []
    
    def validate_file(self, file):
        """
        Validate the uploaded file format and structure
        """
        try:
            # Check file extension
            if not file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
                raise ValidationError("File must be Excel (.xlsx, .xls) or CSV format")
            
            # Read file based on extension
            if file.name.lower().endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file.read()))
            else:
                df = pd.read_excel(io.BytesIO(file.read()))
            
            # Reset file pointer
            file.seek(0)
            
            # Check if file is empty
            if df.empty:
                raise ValidationError("File is empty")
            
            # Check for required columns
            missing_columns = []
            for col in self.REQUIRED_COLUMNS:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
            
            return df
            
        except Exception as e:
            raise ValidationError(f"Error reading file: {str(e)}")
    
    def clean_data(self, df):
        """
        Clean and standardize the data
        """
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Strip whitespace from string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
        
        # Standardize column names (handle variations)
        column_mapping = {
            'firstname': 'first_name',
            'first name': 'first_name',
            'fname': 'first_name',
            'lastname': 'last_name', 
            'last name': 'last_name',
            'lname': 'last_name',
            'email address': 'email',
            'email_address': 'email',
            'learner reference number': 'lrn',
            'lrn number': 'lrn',
            'grade': 'grade_level',
            'grade level': 'grade_level',
            'class': 'section',
            'section name': 'section',
            'middlename': 'middle_name',
            'middle name': 'middle_name',
            'mname': 'middle_name',
            'date of birth': 'date_of_birth',
            'dob': 'date_of_birth',
            'birthday': 'date_of_birth',
            'phone': 'phone_number',
            'phone number': 'phone_number',
            'contact number': 'phone_number',
            'parent name': 'parent_name',
            'parent_name': 'parent_name',
            'guardian name': 'parent_name',
            'parent phone': 'parent_phone',
            'parent_phone': 'parent_phone',
            'guardian phone': 'parent_phone',
            'parent email': 'parent_email',
            'parent_email': 'parent_email',
            'guardian email': 'parent_email',
            'emergency contact': 'emergency_contact',
            'emergency_contact': 'emergency_contact',
            'emergency phone': 'emergency_phone',
            'emergency_phone': 'emergency_phone',
            'blood type': 'blood_type',
            'blood_type': 'blood_type',
            'medical conditions': 'medical_conditions',
            'medical_conditions': 'medical_conditions',
            'health conditions': 'medical_conditions'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        return df
    
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
            df = self.validate_file(file)
            
            # Clean data
            df = self.clean_data(df)
            
            # Process each row
            for index, row in df.iterrows():
                row_number = index + 2  # +2 because Excel is 1-indexed and has header
                row_data = row.to_dict()
                
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
