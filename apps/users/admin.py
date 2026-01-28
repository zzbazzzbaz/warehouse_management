from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'phone', 'is_admin', 'is_active', 'created_at']
    list_filter = ['is_admin', 'is_active', 'created_at']
    search_fields = ['username', 'phone']
    ordering = ['-created_at']
    list_per_page = 20
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('phone', 'address')}),
        ('状态', {'fields': ('is_active', 'is_admin')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone', 'password1', 'password2', 'is_active', 'is_admin'),
        }),
    )
