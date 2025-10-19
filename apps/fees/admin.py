from django.contrib import admin
from .models import FeeStructure


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'is_active')
    list_filter = ('is_active',)
