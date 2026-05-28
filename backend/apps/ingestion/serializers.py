"""Ingestion serializers"""
from rest_framework import serializers
from apps.emissions.models import SourceFile


class SourceFileSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    success_rate = serializers.ReadOnlyField()

    class Meta:
        model = SourceFile
        fields = [
            'id', 'source_type', 'original_filename', 'file_size_bytes',
            'status', 'total_rows', 'processed_rows', 'flagged_rows', 'failed_rows',
            'success_rate', 'ingestion_timestamp', 'processing_started_at',
            'processing_completed_at', 'error_message', 'uploaded_by_name',
            'detected_columns', 'column_mapping_used',
        ]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.full_name if obj.uploaded_by else None


class SourceFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    source_type = serializers.ChoiceField(choices=SourceFile.SourceType.choices)

    def validate_file(self, value):
        allowed_types = ['.csv', '.xlsx', '.xls']
        name = value.name.lower()
        if not any(name.endswith(ext) for ext in allowed_types):
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
            )
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError("File too large. Maximum size is 50MB.")
        return value
