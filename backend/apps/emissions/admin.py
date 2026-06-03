"""
Django Admin configuration for the Emissions app.
Registers SourceFile and EmissionRecord with rich admin views.
"""
from django.contrib import admin
from .models import SourceFile, EmissionRecord


# ---------------------------------------------------------------------------
# SourceFile
# ---------------------------------------------------------------------------
@admin.register(SourceFile)
class SourceFileAdmin(admin.ModelAdmin):
    """Admin for uploaded ESG data files."""

    list_display = (
        'original_filename', 'source_type', 'tenant',
        'uploaded_by', 'status', 'total_rows',
        'processed_rows', 'flagged_rows', 'display_success_rate',
        'ingestion_timestamp',
    )
    list_filter = ('status', 'source_type', 'tenant')
    search_fields = ('original_filename', 'tenant__name')
    ordering = ('-ingestion_timestamp',)
    date_hierarchy = 'ingestion_timestamp'

    fieldsets = (
        (None, {
            'fields': (
                'tenant', 'uploaded_by', 'source_type',
                'original_filename', 'file_path', 'file_size_bytes', 'status',
            ),
        }),
        ('Processing Statistics', {
            'fields': (
                'total_rows', 'processed_rows',
                'flagged_rows', 'failed_rows',
            ),
        }),
        ('Timing', {
            'fields': (
                'ingestion_timestamp',
                'processing_started_at',
                'processing_completed_at',
            ),
            'classes': ('collapse',),
        }),
        ('Column Mapping', {
            'fields': ('detected_columns', 'column_mapping_used'),
            'classes': ('collapse',),
        }),
        ('Errors', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('ingestion_timestamp',)

    @admin.display(description='Success %')
    def display_success_rate(self, obj):
        return f"{obj.success_rate}%"


# ---------------------------------------------------------------------------
# EmissionRecord
# ---------------------------------------------------------------------------
@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    """Admin for canonical ESG emission records."""

    list_display = (
        'short_id', 'tenant', 'source_type', 'scope_category',
        'activity_category', 'activity_date', 'quantity',
        'calculated_emissions', 'status', 'suspicious_flag',
    )
    list_filter = (
        'status', 'scope_category', 'activity_category',
        'suspicious_flag', 'is_duplicate', 'tenant',
    )
    search_fields = (
        'source_identifier', 'location', 'department',
        'vendor', 'tenant__name',
    )
    ordering = ('-created_at',)
    date_hierarchy = 'activity_date'
    list_per_page = 50

    fieldsets = (
        ('Identity', {
            'fields': (
                'tenant', 'source_file', 'status',
                'scope_category', 'activity_category', 'source_type',
            ),
        }),
        ('Activity Data', {
            'fields': (
                'activity_date', 'quantity', 'raw_unit',
                'normalized_quantity', 'normalized_unit',
            ),
        }),
        ('Source Info', {
            'fields': (
                'source_identifier', 'location',
                'department', 'cost_center', 'vendor',
            ),
            'classes': ('collapse',),
        }),
        ('Emissions Calculation', {
            'fields': (
                'emission_factor', 'emission_factor_source',
                'calculated_emissions', 'calculated_emissions_unit',
            ),
        }),
        ('Quality Flags', {
            'fields': (
                'suspicious_flag', 'suspicious_reasons',
                'validation_errors', 'is_duplicate', 'duplicate_of',
            ),
            'classes': ('collapse',),
        }),
        ('Analyst Workflow', {
            'fields': (
                'analyst_notes', 'reviewed_by', 'reviewed_at',
                'approved_by', 'approved_at',
                'rejected_reason', 'locked_at',
            ),
            'classes': ('collapse',),
        }),
        ('Original Data', {
            'fields': ('original_payload', 'row_number'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='ID')
    def short_id(self, obj):
        return str(obj.id)[:8]
