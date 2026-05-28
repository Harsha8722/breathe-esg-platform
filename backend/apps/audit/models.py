"""
Audit trail model - immutable record of all significant state changes.
"""
from django.db import models
import uuid


class AuditLog(models.Model):
    class Action(models.TextChoices):
        FILE_UPLOADED = 'file_uploaded', 'File Uploaded'
        INGESTION_STARTED = 'ingestion_started', 'Ingestion Started'
        INGESTION_COMPLETED = 'ingestion_completed', 'Ingestion Completed'
        INGESTION_FAILED = 'ingestion_failed', 'Ingestion Failed'
        RECORD_FLAGGED = 'record_flagged', 'Record Flagged'
        RECORD_APPROVED = 'record_approved', 'Record Approved'
        RECORD_REJECTED = 'record_rejected', 'Record Rejected'
        RECORD_LOCKED = 'record_locked', 'Record Locked'
        RECORD_EDITED = 'record_edited', 'Record Edited'
        NOTE_ADDED = 'note_added', 'Note Added'
        BULK_APPROVED = 'bulk_approved', 'Bulk Approved'
        BULK_REJECTED = 'bulk_rejected', 'Bulk Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(
        'authentication.User', on_delete=models.SET_NULL, null=True,
        related_name='audit_actions'
    )
    action = models.CharField(max_length=50, choices=Action.choices)

    # Target object (generic - can be SourceFile or EmissionRecord)
    target_type = models.CharField(max_length=50)  # 'source_file', 'emission_record'
    target_id = models.CharField(max_length=100)
    target_repr = models.CharField(max_length=500, blank=True)

    # Change data
    before_state = models.JSONField(default=dict, blank=True)
    after_state = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['actor', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor} at {self.timestamp}"
