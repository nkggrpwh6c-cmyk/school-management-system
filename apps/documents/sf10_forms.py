from django import forms
from .sf10_models import SF10Document, SF10Grade, SF10Attendance, SF10Upload

class SF10DocumentForm(forms.ModelForm):
    class Meta:
        model = SF10Document
        fields = [
            'school_year', 'grade_level', 'section', 'lrn', 'name', 'birth_date', 'birth_place',
            'sex', 'age', 'present_address', 'permanent_address', 'contact_number', 'email',
            'father_name', 'father_occupation', 'father_contact', 'mother_name', 'mother_occupation',
            'mother_contact', 'guardian_name', 'guardian_relationship', 'guardian_contact',
            'previous_school', 'previous_grade', 'date_of_enrollment', 'date_of_graduation',
            'status', 'is_complete', 'notes'
        ]
        widgets = {
            'school_year': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_level': forms.TextInput(attrs={'class': 'form-control'}),
            'section': forms.TextInput(attrs={'class': 'form-control'}),
            'lrn': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'birth_place': forms.TextInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'present_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permanent_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'father_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control'}),
            'previous_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_enrollment': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_of_graduation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_complete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SF10GradeForm(forms.ModelForm):
    class Meta:
        model = SF10Grade
        fields = ['subject', 'first_quarter', 'second_quarter', 'third_quarter', 'fourth_quarter', 'final_grade', 'remarks']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'first_quarter': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'second_quarter': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'third_quarter': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fourth_quarter': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'final_grade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SF10AttendanceForm(forms.ModelForm):
    class Meta:
        model = SF10Attendance
        fields = ['month', 'days_present', 'days_absent', 'days_tardy']
        widgets = {
            'month': forms.TextInput(attrs={'class': 'form-control'}),
            'days_present': forms.NumberInput(attrs={'class': 'form-control'}),
            'days_absent': forms.NumberInput(attrs={'class': 'form-control'}),
            'days_tardy': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SF10UploadForm(forms.ModelForm):
    class Meta:
        model = SF10Upload
        fields = ['name', 'excel_file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'excel_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
        }

class SF10SearchForm(forms.Form):
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, LRN, or school year...'
        })
    )
    
    school_year = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'School Year (e.g., 2023-2024)'
        })
    )
    
    grade_level = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Grade Level (e.g., Grade 12)'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + SF10Document.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
