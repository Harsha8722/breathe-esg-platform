"""Ingestion views - file upload and status endpoints"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone

from apps.emissions.models import SourceFile
from apps.ingestion.serializers import SourceFileSerializer, SourceFileUploadSerializer
from apps.ingestion.services import IngestionService
from utils.audit_service import AuditService
import threading
import logging

logger = logging.getLogger(__name__)


class SourceFileListView(generics.ListAPIView):
    serializer_class = SourceFileSerializer

    def get_queryset(self):
        qs = SourceFile.objects.filter(tenant=self.request.tenant)
        source_type = self.request.query_params.get('source_type')
        status_filter = self.request.query_params.get('status')
        if source_type:
            qs = qs.filter(source_type=source_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.select_related('uploaded_by')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})


class SourceFileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if not request.user.can_upload():
            return Response({'success': False, 'error': {'message': 'Permission denied'}}, status=403)

        if not request.tenant:
            return Response({'success': False, 'error': {'message': 'Tenant context required'}}, status=400)

        serializer = SourceFileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        source_type = serializer.validated_data['source_type']

        logger.info(
            f"[UploadView] File upload received: filename={uploaded_file.name}, "
            f"source_type={source_type}, user={request.user}, "
            f"tenant={request.tenant}, size={uploaded_file.size} bytes"
        )

        sf = SourceFile.objects.create(
            tenant=request.tenant,
            uploaded_by=request.user,
            source_type=source_type,
            original_filename=uploaded_file.name,
            file_path=uploaded_file,
            file_size_bytes=uploaded_file.size,
            status=SourceFile.Status.PENDING,
        )

        AuditService.log_file_upload(request.tenant, request.user, sf, request)

        # Process asynchronously in background thread (use Celery in production)
        def run_ingestion():
            try:
                svc = IngestionService(sf, actor=request.user)
                svc.run()
                logger.info(
                    f"[UploadView] Async ingestion completed successfully "
                    f"for file={sf.original_filename}, id={sf.id}"
                )
            except ValueError as e:
                # Validation errors (missing columns, bad file format) are expected
                logger.warning(
                    f"[UploadView] Ingestion validation error for "
                    f"file={sf.original_filename}: {e}"
                )
            except Exception as e:
                logger.exception(
                    f"[UploadView] Async ingestion failed for "
                    f"file={sf.original_filename}: {e}"
                )

        thread = threading.Thread(target=run_ingestion, daemon=True)
        thread.start()

        return Response({
            'success': True,
            'data': SourceFileSerializer(sf).data,
            'message': 'File uploaded and queued for processing'
        }, status=status.HTTP_202_ACCEPTED)


class SourceFileDetailView(generics.RetrieveAPIView):
    serializer_class = SourceFileSerializer

    def get_queryset(self):
        return SourceFile.objects.filter(tenant=self.request.tenant)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})
