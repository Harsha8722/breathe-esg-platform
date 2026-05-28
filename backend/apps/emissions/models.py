"""
Core ESG data models: SourceFile, EmissionRecord, AuditLog.
These are the heart of the platform.
"""
from django.db import models
import uuid
import json


class SourceFile(models.Model):
    """
    Represents an uploaded ESG data file. Tracks ingestion status and metadata.
    """
    class SourceType(models.TextChoices):
        SAP_FUEL = 'sap_fuel', 'SAP Fuel/Procurement'
        UTILITY_ELECTRICITY = 'utility_electricity', 'Utility Electricity'
        CORPORATE_TRAVEL = 'corporate_travel', 'Corporate Travel'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        PROCESSED = 'processed', 'Processed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='source_files')
    uploaded_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    source_type = models.CharField(max_length=50, choices=SourceType.choices)
    original_filename = models.CharField(max_length=500)
    file_path = models.FileField(upload_to='uploads/%Y/%m/', max_length=500)
    file_size_bytes = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Processing stats
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    flagged_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)

    # Metadata
    ingestion_timestamp = models.DateTimeField(auto_now_add=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Raw column map detected during ingestion
    detected_columns = models.JSONField(default=list)
    column_mapping_used = models.JSONField(default=dict)

    class Meta:
        db_table = 'source_files'
        ordering = ['-ingestion_timestamp']

    def __str__(self):
        return f"{self.original_filename} ({self.source_type})"

    @property
    def success_rate(self):
        if self.total_rows == 0:
            return 0
        return round((self.processed_rows / self.total_rows) * 100, 1)


class EmissionRecord(models.Model):
    """
    Canonical ESG emission record. The normalized, validated, source-of-truth row.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        FLAGGED = 'flagged', 'Flagged - Needs Attention'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        LOCKED = 'locked', 'Locked'

    class ScopeCategory(models.TextChoices):
        SCOPE_1 = 'scope_1', 'Scope 1 - Direct Emissions'
        SCOPE_2 = 'scope_2', 'Scope 2 - Indirect (Energy)'
        SCOPE_3 = 'scope_3', 'Scope 3 - Value Chain'

    class ActivityCategory(models.TextChoices):
        STATIONARY_COMBUSTION = 'stationary_combustion', 'Stationary Combustion'
        MOBILE_COMBUSTION = 'mobile_combustion', 'Mobile Combustion'
        PURCHASED_ELECTRICITY = 'purchased_electricity', 'Purchased Electricity'
        BUSINESS_TRAVEL = 'business_travel', 'Business Travel'
        EMPLOYEE_COMMUTE = 'employee_commute', 'Employee Commute'
        UPSTREAM_TRANSPORT = 'upstream_transport', 'Upstream Transport'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='emission_records')
    source_file = models.ForeignKey(SourceFile, on_delete=models.CASCADE, related_name='records')

    # Record identity
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    scope_category = models.CharField(max_length=20, choices=ScopeCategory.choices)
    activity_category = models.CharField(max_length=50, choices=ActivityCategory.choices)
    source_type = models.CharField(max_length=50)  # sap_fuel, utility_electricity, corporate_travel

    # Activity data (raw extracted)
    activity_date = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    raw_unit = models.CharField(max_length=50, blank=True)
    normalized_unit = models.CharField(max_length=50, blank=True)
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    # Source identifiers
    source_identifier = models.CharField(max_length=500, blank=True)  # meter ID, plant code, etc.
    location = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    vendor = models.CharField(max_length=200, blank=True)

    # Emissions calculation
    emission_factor = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    emission_factor_source = models.CharField(max_length=200, blank=True)
    calculated_emissions = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)  # kgCO2e
    calculated_emissions_unit = models.CharField(max_length=20, default='kgCO2e')

    # Quality flags
    suspicious_flag = models.BooleanField(default=False)
    suspicious_reasons = models.JSONField(default=list)
    validation_errors = models.JSONField(default=list)
    is_duplicate = models.BooleanField(default=False)
    duplicate_of = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='duplicates')

    # Analyst workflow
    analyst_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        'authentication.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_records'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'authentication.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_records'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_reason = models.TextField(blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    # Original source data (preserved for audit)
    original_payload = models.JSONField(default=dict)
    row_number = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'emission_records'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'scope_category']),
            models.Index(fields=['source_file', 'status']),
            models.Index(fields=['suspicious_flag']),
            models.Index(fields=['activity_date']),
        ]

    def __str__(self):
        return f"{self.source_type} | {self.activity_date} | {self.status}"

    def is_editable(self):
        return self.status not in [self.Status.LOCKED, self.Status.APPROVED]

    def lock(self, user=None):
        from django.utils import timezone
        self.status = self.Status.LOCKED
        self.locked_at = timezone.now()
        self.save(update_fields=['status', 'locked_at', 'updated_at'])
