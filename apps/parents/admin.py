from django.contrib import admin
from .models import Parent


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('parent_id', 'user', 'occupation', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('parent_id', 'user__first_name', 'user__last_name')
