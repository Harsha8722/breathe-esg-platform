"""Audit trail views and serializers"""
from rest_framework import generics
from rest_framework.response import Response
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'target_type', 'target_id', 'target_repr',
            'before_state', 'after_state', 'metadata', 'notes',
            'actor_name', 'ip_address', 'timestamp',
        ]

    def get_actor_name(self, obj):
        return obj.actor.full_name if obj.actor else 'System'


class AuditLogFilter(django_filters.FilterSet):
    action = django_filters.CharFilter(lookup_expr='iexact')
    target_type = django_filters.CharFilter(lookup_expr='iexact')
    target_id = django_filters.CharFilter(lookup_expr='iexact')
    date_from = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model = AuditLog
        fields = []


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    filterset_class = AuditLogFilter
    search_fields = ['target_repr', 'notes', 'action']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        return AuditLog.objects.filter(
            tenant=self.request.tenant
        ).select_related('actor')

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response({'success': True, 'data': self.get_serializer(qs, many=True).data})
