"""Emissions record serializers"""
from rest_framework import serializers
from apps.emissions.models import EmissionRecord, SourceFile
from apps.authentication.serializers import UserSerializer


class EmissionRecordListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    approved_by_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    suspicious_reasons = serializers.SerializerMethodField()
    validation_errors = serializers.SerializerMethodField()

    class Meta:
        model = EmissionRecord
        fields = [
            'id', 'status', 'scope_category', 'activity_category', 'source_type',
            'activity_date', 'quantity', 'raw_unit', 'normalized_quantity', 'normalized_unit',
            'calculated_emissions', 'calculated_emissions_unit',
            'suspicious_flag', 'is_duplicate', 'source_identifier', 'location',
            'vendor', 'analyst_notes', 'validation_errors', 'suspicious_reasons',
            'approved_by_name', 'reviewed_by_name', 'approved_at', 'reviewed_at',
            'created_at', 'row_number',
        ]

    def get_approved_by_name(self, obj):
        return obj.approved_by.full_name if obj.approved_by else None

    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.full_name if obj.reviewed_by else None

    def get_suspicious_reasons(self, obj):
        # Defensive: old rows or manual edits may store NULL.
        val = getattr(obj, 'suspicious_reasons', None)
        if isinstance(val, list):
            return val
        return []

    def get_validation_errors(self, obj):
        val = getattr(obj, 'validation_errors', None)
        if isinstance(val, list):
            return val
        return []


class EmissionRecordDetailSerializer(EmissionRecordListSerializer):
    """Full detail serializer with original payload."""

    class Meta(EmissionRecordListSerializer.Meta):
        fields = EmissionRecordListSerializer.Meta.fields + [
            'emission_factor', 'emission_factor_source',
            'cost_center', 'department',
            'original_payload', 'locked_at', 'rejected_reason',
            'duplicate_of', 'updated_at',
        ]


class RecordReviewSerializer(serializers.Serializer):
    """Analyst action: approve, reject, add note"""
    action = serializers.ChoiceField(choices=['approve', 'reject', 'note', 'flag', 'unflag'])
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    rejected_reason = serializers.CharField(required=False, allow_blank=True)


class BulkActionSerializer(serializers.Serializer):
    record_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=500,
    )
    action = serializers.ChoiceField(choices=['approve', 'reject', 'lock'])
    notes = serializers.CharField(required=False, allow_blank=True)
