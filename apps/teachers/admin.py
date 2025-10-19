from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'user', 'employee_id', 'hire_date', 'is_active')
    list_filter = ('is_active', 'hire_date')
    search_fields = ('teacher_id', 'employee_id', 'user__first_name', 'user__last_name')
