"""
Ingestion orchestration service.
Coordinates file parsing → record creation → suspicious detection → audit logging.
"""
import logging
from django.utils import timezone
from django.db import transaction

from apps.emissions.models import SourceFile, EmissionRecord
from apps.ingestion.parsers import SAPFuelParser, UtilityElectricityParser, CorporateTravelParser
from apps.ingestion.suspicious_detector import SuspiciousRowDetector
from utils.audit_service import AuditService
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

PARSER_MAP = {
    SourceFile.SourceType.SAP_FUEL: SAPFuelParser,
    SourceFile.SourceType.UTILITY_ELECTRICITY: UtilityElectricityParser,
    SourceFile.SourceType.CORPORATE_TRAVEL: CorporateTravelParser,
}


class IngestionService:
    def __init__(self, source_file: SourceFile, actor=None):
        self.source_file = source_file
        self.actor = actor

    def run(self):
        sf = self.source_file
        sf.status = SourceFile.Status.PROCESSING
        sf.processing_started_at = timezone.now()
        sf.save(update_fields=['status', 'processing_started_at'])

        AuditService.log(
            tenant=sf.tenant, actor=self.actor,
            action=AuditLog.Action.INGESTION_STARTED,
            target_type='source_file', target_id=str(sf.id),
            target_repr=sf.original_filename,
        )

        try:
            ParserClass = PARSER_MAP.get(sf.source_type)
            if not ParserClass:
                raise ValueError(f"No parser for source type: {sf.source_type}")

            parser = ParserClass(sf)
            raw_records = parser.parse(sf.file_path.path)

            # Statistical suspicious detection
            detector = SuspiciousRowDetector()
            analyzed_records = detector.analyze_batch(raw_records)

            # Persist records in bulk
            stats = self._persist_records(analyzed_records)

            sf.total_rows = stats['total']
            sf.processed_rows = stats['processed']
            sf.flagged_rows = stats['flagged']
            sf.failed_rows = stats['failed']
            sf.status = SourceFile.Status.PROCESSED
            sf.processing_completed_at = timezone.now()
            sf.save(update_fields=[
                'total_rows', 'processed_rows', 'flagged_rows', 'failed_rows',
                'status', 'processing_completed_at'
            ])

            AuditService.log(
                tenant=sf.tenant, actor=self.actor,
                action=AuditLog.Action.INGESTION_COMPLETED,
                target_type='source_file', target_id=str(sf.id),
                target_repr=sf.original_filename,
                metadata=stats,
            )
            return stats

        except Exception as e:
            logger.exception(f"Ingestion failed for {sf.id}: {e}")
            sf.status = SourceFile.Status.FAILED
            sf.error_message = str(e)[:2000]
            sf.processing_completed_at = timezone.now()
            sf.save(update_fields=['status', 'error_message', 'processing_completed_at'])

            AuditService.log(
                tenant=sf.tenant, actor=self.actor,
                action=AuditLog.Action.INGESTION_FAILED,
                target_type='source_file', target_id=str(sf.id),
                metadata={'error': str(e)},
            )
            raise

    @transaction.atomic
    def _persist_records(self, raw_records: list) -> dict:
        stats = {'total': len(raw_records), 'processed': 0, 'flagged': 0, 'failed': 0}
        to_create = []

        for r in raw_records:
            try:
                status = (
                    EmissionRecord.Status.FLAGGED
                    if r.get('suspicious_flag') or r.get('validation_errors')
                    else EmissionRecord.Status.PENDING
                )

                record = EmissionRecord(
                    tenant=self.source_file.tenant,
                    source_file=self.source_file,
                    status=status,
                    scope_category=r.get('scope_category', 'scope_3'),
                    activity_category=r.get('activity_category', 'business_travel'),
                    source_type=r.get('source_type', ''),
                    activity_date=r.get('activity_date'),
                    quantity=r.get('quantity'),
                    raw_unit=r.get('raw_unit', ''),
                    normalized_unit=r.get('normalized_unit', ''),
                    normalized_quantity=r.get('normalized_quantity'),
                    source_identifier=str(r.get('source_identifier', ''))[:500],
                    location=str(r.get('location', ''))[:200],
                    cost_center=str(r.get('cost_center', ''))[:100],
                    vendor=str(r.get('vendor', ''))[:200],
                    emission_factor=r.get('emission_factor'),
                    emission_factor_source=str(r.get('emission_factor_source', ''))[:200],
                    calculated_emissions=r.get('calculated_emissions'),
                    suspicious_flag=r.get('suspicious_flag', False),
                    suspicious_reasons=r.get('suspicious_reasons', []),
                    validation_errors=r.get('validation_errors', []),
                    is_duplicate=r.get('is_duplicate', False),
                    original_payload=r.get('original_payload', {}),
                    row_number=r.get('row_number', 0),
                )
                to_create.append(record)
                stats['processed'] += 1
                if r.get('suspicious_flag'):
                    stats['flagged'] += 1

            except Exception as e:
                logger.warning(f"Row {r.get('row_number')} failed: {e}")
                stats['failed'] += 1

        EmissionRecord.objects.bulk_create(to_create, batch_size=500)
        return stats
