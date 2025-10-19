"""
Forms for bulk import functionality
"""
from django import forms
from django.core.exceptions import ValidationError
from .bulk_import import StudentBulkImporter


class BulkImportForm(forms.Form):
    """
    Form for bulk import file upload
    """
    file = forms.FileField(
        label='Select File',
        help_text='Upload CSV file (.csv)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )
    
    grade_level = forms.ChoiceField(
        label='Grade Level',
        choices=[(i, f'Grade {i}') for i in range(1, 13)],
        required=False,
        help_text='Set default grade level for all students (optional)',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    section = forms.CharField(
        label='Section',
        max_length=100,
        required=False,
        help_text='Set default section for all students (optional)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    send_credentials = forms.BooleanField(
        label='Send Login Credentials',
        required=False,
        initial=True,
        help_text='Email login credentials to students and parents',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise ValidationError('Please select a file to upload')
        
        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError('File size must be less than 10MB')
        
        # Validate file format
        if not file.name.lower().endswith('.csv'):
            raise ValidationError('File must be CSV format')
        
        return file


class ImportPreviewForm(forms.Form):
    """
    Form for confirming import after preview
    """
    confirm_import = forms.BooleanField(
        label='Confirm Import',
        required=True,
        help_text='Check this box to confirm the import of students',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    skip_errors = forms.BooleanField(
        label='Skip Rows with Errors',
        required=False,
        initial=True,
        help_text='Import only valid rows and skip rows with errors',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class ImportTemplateForm(forms.Form):
    """
    Form for downloading import template
    """
    template_type = forms.ChoiceField(
        label='Template Type',
        choices=[
            ('basic', 'Basic Template (Required fields only)'),
            ('complete', 'Complete Template (All fields)'),
            ('sample', 'Sample Data Template')
        ],
        initial='complete',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    grade_level = forms.ChoiceField(
        label='Default Grade Level',
        choices=[('', 'No default')] + [(i, f'Grade {i}') for i in range(1, 13)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    section = forms.CharField(
        label='Default Section',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
