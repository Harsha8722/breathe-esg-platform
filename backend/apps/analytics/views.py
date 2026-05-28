"""Analytics views - scope breakdowns, trend data, source summaries"""
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncMonth, TruncYear

from apps.emissions.models import EmissionRecord, SourceFile


class ScopeTrendView(APIView):
    """Monthly emissions trend by scope."""

    def get(self, request):
        tenant = request.tenant
        year = request.query_params.get('year', '2024')

        qs = EmissionRecord.objects.filter(
            tenant=tenant,
            status__in=[EmissionRecord.Status.APPROVED, EmissionRecord.Status.LOCKED],
            activity_date__year=year,
        ).annotate(month=TruncMonth('activity_date')).values('month', 'scope_category').annotate(
            total_emissions=Sum('calculated_emissions'),
            record_count=Count('id'),
        ).order_by('month', 'scope_category')

        data = list(qs)
        for d in data:
            d['month'] = d['month'].strftime('%Y-%m') if d['month'] else None
            d['total_emissions'] = float(d['total_emissions'] or 0)

        return Response({'success': True, 'data': data})


class SourceTypeBreakdownView(APIView):
    """Emissions breakdown by source type."""

    def get(self, request):
        tenant = request.tenant
        qs = EmissionRecord.objects.filter(
            tenant=tenant,
            status__in=[EmissionRecord.Status.APPROVED, EmissionRecord.Status.LOCKED],
        ).values('source_type').annotate(
            total_emissions=Sum('calculated_emissions'),
            record_count=Count('id'),
        ).order_by('-total_emissions')

        data = [
            {
                'source_type': d['source_type'],
                'total_emissions_kgco2e': float(d['total_emissions'] or 0),
                'record_count': d['record_count'],
            }
            for d in qs
        ]
        return Response({'success': True, 'data': data})


class IngestionStatsView(APIView):
    """File upload and processing statistics."""

    def get(self, request):
        tenant = request.tenant
        qs = SourceFile.objects.filter(tenant=tenant)

        stats = qs.aggregate(
            total_files=Count('id'),
            total_rows=Sum('total_rows'),
            processed_rows=Sum('processed_rows'),
            flagged_rows=Sum('flagged_rows'),
            failed_rows=Sum('failed_rows'),
        )

        by_type = list(
            qs.values('source_type', 'status').annotate(count=Count('id')).order_by('source_type')
        )

        return Response({
            'success': True,
            'data': {
                'aggregate': stats,
                'by_type_and_status': by_type,
            }
        })
