"""
Django Admin configuration for the Authentication app.
Registers the custom User model with full admin support.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for the User model. Uses email instead of username
    and exposes tenant/role fields.
    """

    # List display
    list_display = (
        'email', 'first_name', 'last_name', 'role',
        'tenant', 'is_active', 'is_staff', 'created_at',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'tenant')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)

    # Detail view fieldsets
    fieldsets = (
        (None, {
            'fields': ('email', 'password'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name'),
        }),
        ('Organisation', {
            'fields': ('tenant', 'role'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Security', {
            'fields': ('last_login', 'last_login_ip'),
            'classes': ('collapse',),
        }),
    )

    # Fieldsets used when creating a new user via Admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name',
                'password1', 'password2',
                'role', 'tenant', 'is_active', 'is_staff',
            ),
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'last_login')
