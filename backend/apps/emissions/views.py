"""
Emissions views - review queue, analyst actions, bulk operations.
"""
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
import django_filters

from apps.emissions.models import EmissionRecord
from apps.emissions.serializers import (
    EmissionRecordListSerializer, EmissionRecordDetailSerializer,
    RecordReviewSerializer, BulkActionSerializer
)
from utils.audit_service import AuditService
from apps.audit.models import AuditLog


class EmissionRecordFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(choices=EmissionRecord.Status.choices)
    scope_category = django_filters.MultipleChoiceFilter(choices=EmissionRecord.ScopeCategory.choices)
    activity_category = django_filters.MultipleChoiceFilter(choices=EmissionRecord.ActivityCategory.choices)
    source_type = django_filters.CharFilter(lookup_expr='iexact')
    suspicious_flag = django_filters.BooleanFilter()
    is_duplicate = django_filters.BooleanFilter()
    date_from = django_filters.DateFilter(field_name='activity_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='activity_date', lookup_expr='lte')
    source_file = django_filters.UUIDFilter(field_name='source_file__id')

    class Meta:
        model = EmissionRecord
        fields = []


class EmissionRecordListView(generics.ListAPIView):
    serializer_class = EmissionRecordListSerializer
    filterset_class = EmissionRecordFilter
    search_fields = ['source_identifier', 'location', 'vendor', 'analyst_notes']
    ordering_fields = ['activity_date', 'calculated_emissions', 'created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        return EmissionRecord.objects.filter(
            tenant=self.request.tenant
        ).select_related('reviewed_by', 'approved_by', 'source_file')

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response({'success': True, 'data': serializer.data})


class EmissionRecordDetailView(generics.RetrieveAPIView):
    serializer_class = EmissionRecordDetailSerializer

    def get_queryset(self):
        return EmissionRecord.objects.filter(tenant=self.request.tenant)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({'success': True, 'data': self.get_serializer(instance).data})


class RecordReviewView(APIView):
    """Handle analyst review actions: approve, reject, flag, note."""

    def post(self, request, pk):
        try:
            record = EmissionRecord.objects.get(id=pk, tenant=request.tenant)
        except EmissionRecord.DoesNotExist:
            return Response({'success': False, 'error': {'message': 'Record not found'}}, status=404)

        if record.status == EmissionRecord.Status.LOCKED:
            return Response({'success': False, 'error': {'message': 'Record is locked and cannot be modified'}}, status=403)

        serializer = RecordReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        action = data['action']
        notes = data.get('notes', '')
        old_status = record.status

        with transaction.atomic():
            if action == 'approve':
                if not request.user.can_approve():
                    return Response({'success': False, 'error': {'message': 'Insufficient permissions to approve'}}, status=403)
                record.status = EmissionRecord.Status.APPROVED
                record.approved_by = request.user
                record.approved_at = timezone.now()
                record.analyst_notes = notes or record.analyst_notes

            elif action == 'reject':
                if not request.user.can_approve():
                    return Response({'success': False, 'error': {'message': 'Insufficient permissions to reject'}}, status=403)
                record.status = EmissionRecord.Status.REJECTED
                record.rejected_reason = data.get('rejected_reason', notes)
                record.reviewed_by = request.user
                record.reviewed_at = timezone.now()

            elif action == 'note':
                record.analyst_notes = notes
                record.reviewed_by = request.user
                record.reviewed_at = timezone.now()

            elif action == 'flag':
                record.suspicious_flag = True
                record.status = EmissionRecord.Status.FLAGGED
                if notes:
                    record.suspicious_reasons = record.suspicious_reasons + [f"Manual: {notes}"]

            elif action == 'unflag':
                record.suspicious_flag = False
                if record.status == EmissionRecord.Status.FLAGGED:
                    record.status = EmissionRecord.Status.PENDING

            record.save()

            AuditService.log_record_status_change(
                tenant=request.tenant,
                actor=request.user,
                record=record,
                old_status=old_status,
                new_status=record.status,
                notes=notes,
                request=request,
            )

        return Response({
            'success': True,
            'data': EmissionRecordDetailSerializer(record).data,
            'message': f'Record {action}d successfully'
        })


class BulkActionView(APIView):
    """Bulk approve / reject / lock operations."""

    def post(self, request):
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data['action'] in ('approve', 'reject', 'lock') and not request.user.can_approve():
            return Response({'success': False, 'error': {'message': 'Insufficient permissions'}}, status=403)

        record_ids = data['record_ids']
        action = data['action']
        notes = data.get('notes', '')

        records = EmissionRecord.objects.filter(
            id__in=record_ids,
            tenant=request.tenant,
        ).exclude(status=EmissionRecord.Status.LOCKED)

        updated_count = 0
        with transaction.atomic():
            for record in records:
                old_status = record.status
                if action == 'approve':
                    record.status = EmissionRecord.Status.APPROVED
                    record.approved_by = request.user
                    record.approved_at = timezone.now()
                elif action == 'reject':
                    record.status = EmissionRecord.Status.REJECTED
                    record.rejected_reason = notes
                elif action == 'lock':
                    record.status = EmissionRecord.Status.LOCKED
                    record.locked_at = timezone.now()

                record.save(update_fields=['status', 'approved_by', 'approved_at',
                                           'rejected_reason', 'locked_at', 'updated_at'])
                updated_count += 1

            # Single bulk audit entry
            AuditService.log(
                tenant=request.tenant,
                actor=request.user,
                action=f'bulk_{action}d',
                target_type='emission_record',
                target_id='bulk',
                metadata={'count': updated_count, 'record_ids': [str(i) for i in record_ids[:20]]},
                notes=notes,
                request=request,
            )

        return Response({
            'success': True,
            'message': f'{updated_count} records {action}d',
            'updated_count': updated_count
        })


class EmissionsSummaryView(APIView):
    """Aggregated summary stats for dashboard."""

    def get(self, request):
        from django.db.models import Sum, Count, Q
        tenant = request.tenant
        qs = EmissionRecord.objects.filter(tenant=tenant)

        summary = {
            'total_records': qs.count(),
            'pending': qs.filter(status=EmissionRecord.Status.PENDING).count(),
            'flagged': qs.filter(status=EmissionRecord.Status.FLAGGED).count(),
            'approved': qs.filter(status=EmissionRecord.Status.APPROVED).count(),
            'rejected': qs.filter(status=EmissionRecord.Status.REJECTED).count(),
            'locked': qs.filter(status=EmissionRecord.Status.LOCKED).count(),
        }

        totals = qs.filter(
            status__in=[EmissionRecord.Status.APPROVED, EmissionRecord.Status.LOCKED]
        ).aggregate(
            scope1=Sum('calculated_emissions', filter=Q(scope_category='scope_1')),
            scope2=Sum('calculated_emissions', filter=Q(scope_category='scope_2')),
            scope3=Sum('calculated_emissions', filter=Q(scope_category='scope_3')),
        )
        summary['total_scope1_kgco2e'] = float(totals['scope1'] or 0)
        summary['total_scope2_kgco2e'] = float(totals['scope2'] or 0)
        summary['total_scope3_kgco2e'] = float(totals['scope3'] or 0)
        summary['total_emissions_kgco2e'] = (
            summary['total_scope1_kgco2e'] +
            summary['total_scope2_kgco2e'] +
            summary['total_scope3_kgco2e']
        )

        return Response({'success': True, 'data': summary})
