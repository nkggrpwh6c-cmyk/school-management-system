from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Student, Attendance, StudentDocument, Grade, Section, AcademicYear
from apps.accounts.models import User


class StudentRegistrationForm(UserCreationForm):
    """
    Student registration form
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=False)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    
    # Student specific fields
    student_id = forms.CharField(max_length=20, required=True)
    admission_number = forms.CharField(max_length=20, required=True)
    admission_date = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    grade = forms.ModelChoiceField(queryset=Grade.objects.filter(is_active=True), required=True)
    section = forms.ModelChoiceField(queryset=Section.objects.filter(is_active=True), required=True)
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.filter(is_current=True), required=True)
    gender = forms.ChoiceField(choices=Student.GENDER_CHOICES, required=True)
    blood_group = forms.CharField(max_length=5, required=False)
    parent_name = forms.CharField(max_length=100, required=True)
    parent_phone = forms.CharField(max_length=15, required=True)
    parent_email = forms.EmailField(required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)
    emergency_contact = forms.CharField(max_length=100, required=False)
    emergency_phone = forms.CharField(max_length=15, required=False)
    medical_conditions = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'date_of_birth', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = 'STUDENT'
        self.fields['role'].widget = forms.HiddenInput()
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'STUDENT'
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.date_of_birth = self.cleaned_data['date_of_birth']
        
        if commit:
            user.save()
            # Create student profile
            Student.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                admission_number=self.cleaned_data['admission_number'],
                admission_date=self.cleaned_data['admission_date'],
                grade=self.cleaned_data['grade'],
                section=self.cleaned_data['section'],
                academic_year=self.cleaned_data['academic_year'],
                gender=self.cleaned_data['gender'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                blood_group=self.cleaned_data['blood_group'],
                parent_name=self.cleaned_data['parent_name'],
                parent_phone=self.cleaned_data['parent_phone'],
                parent_email=self.cleaned_data['parent_email'],
                address=self.cleaned_data['address'],
                emergency_contact=self.cleaned_data['emergency_contact'],
                emergency_phone=self.cleaned_data['emergency_phone'],
                medical_conditions=self.cleaned_data['medical_conditions']
            )
        return user


class StudentUpdateForm(forms.ModelForm):
    """
    Student profile update form
    """
    class Meta:
        model = Student
        fields = [
            'student_id', 'admission_number', 'admission_date', 'grade', 'section', 
            'academic_year', 'gender', 'date_of_birth', 'blood_group', 'parent_name', 
            'parent_phone', 'parent_email', 'address', 'emergency_contact', 
            'emergency_phone', 'medical_conditions', 'is_active'
        ]
        widgets = {
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'medical_conditions': forms.Textarea(attrs={'rows': 3}),
        }


class AttendanceForm(forms.ModelForm):
    """
    Attendance marking form
    """
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(is_active=True)


class StudentDocumentForm(forms.ModelForm):
    """
    Student document upload form
    """
    class Meta:
        model = StudentDocument
        fields = ['document_type', 'title', 'file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class StudentSearchForm(forms.Form):
    """
    Student search form
    """
    search = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Search by name, ID, or admission number...',
        'class': 'form-control'
    }))
    grade = forms.ModelChoiceField(queryset=Grade.objects.filter(is_active=True), required=False, empty_label="All Grades")
    section = forms.ModelChoiceField(queryset=Section.objects.filter(is_active=True), required=False, empty_label="All Sections")
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=False, empty_label="All Years")
    is_active = forms.BooleanField(required=False, initial=True)
