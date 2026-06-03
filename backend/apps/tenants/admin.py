"""
Django Admin configuration for the Tenants app.
"""
from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin view for multi-tenant organisations."""

    list_display = (
        'name', 'slug', 'plan', 'industry',
        'country', 'reporting_year', 'is_active', 'created_at',
    )
    list_filter = ('plan', 'is_active', 'industry', 'country')
    search_fields = ('name', 'slug', 'industry')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'plan', 'is_active'),
        }),
        ('Organisation Details', {
            'fields': ('industry', 'country', 'reporting_year'),
        }),
        ('Settings', {
            'fields': (
                'fiscal_year_start_month',
                'default_currency',
                'emission_factor_version',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')
