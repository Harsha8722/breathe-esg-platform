"""
Django Admin configuration for the Audit app.
AuditLog entries are read-only in Admin — they are an immutable trail.
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only admin for the immutable audit trail."""

    list_display = (
        'timestamp', 'action', 'actor',
        'target_type', 'target_id', 'tenant',
    )
    list_filter = ('action', 'target_type', 'tenant')
    search_fields = (
        'actor__email', 'target_repr',
        'target_id', 'notes',
    )
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    list_per_page = 50

    fieldsets = (
        (None, {
            'fields': ('tenant', 'actor', 'action', 'timestamp'),
        }),
        ('Target', {
            'fields': ('target_type', 'target_id', 'target_repr'),
        }),
        ('Change Data', {
            'fields': ('before_state', 'after_state', 'metadata', 'notes'),
            'classes': ('collapse',),
        }),
        ('Request Context', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',),
        }),
    )

    # Make everything read-only — audit logs must not be edited
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
