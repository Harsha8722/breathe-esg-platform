"""
Audit logging service - creates immutable audit trail entries.
"""
from apps.audit.models import AuditLog
import logging

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def log(
        tenant,
        actor,
        action: str,
        target_type: str,
        target_id: str,
        target_repr: str = '',
        before_state: dict = None,
        after_state: dict = None,
        metadata: dict = None,
        notes: str = '',
        request=None,
    ):
        try:
            ip_address = None
            user_agent = ''
            if request:
                ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                             request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            AuditLog.objects.create(
                tenant=tenant,
                actor=actor,
                action=action,
                target_type=target_type,
                target_id=str(target_id),
                target_repr=target_repr[:500] if target_repr else '',
                before_state=before_state or {},
                after_state=after_state or {},
                metadata=metadata or {},
                notes=notes,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    @staticmethod
    def log_record_status_change(tenant, actor, record, old_status, new_status, notes='', request=None):
        AuditService.log(
            tenant=tenant,
            actor=actor,
            action=f'record_{new_status}',
            target_type='emission_record',
            target_id=str(record.id),
            target_repr=str(record),
            before_state={'status': old_status},
            after_state={'status': new_status},
            notes=notes,
            request=request,
        )

    @staticmethod
    def log_file_upload(tenant, actor, source_file, request=None):
        AuditService.log(
            tenant=tenant,
            actor=actor,
            action=AuditLog.Action.FILE_UPLOADED,
            target_type='source_file',
            target_id=str(source_file.id),
            target_repr=source_file.original_filename,
            metadata={
                'source_type': source_file.source_type,
                'file_size': source_file.file_size_bytes,
            },
            request=request,
        )
