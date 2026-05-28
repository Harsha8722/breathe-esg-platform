"""
Tenant and Audit middleware for multi-tenancy and request logging.
"""
import logging
import time
import json
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Resolves the active tenant from JWT claims or X-Tenant-ID header
    and attaches it to the request object.
    """

    def process_request(self, request):
        request.tenant = None
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                from apps.tenants.models import Tenant
                request.tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            except Exception:
                pass

    def process_view(self, request, view_func, view_args, view_kwargs):
        # After auth, resolve tenant from user if not set
        if not request.tenant and hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'tenant') and request.user.tenant:
                request.tenant = request.user.tenant
        return None


class AuditMiddleware(MiddlewareMixin):
    """
    Logs request/response metadata for sensitive mutation operations.
    """
    AUDITED_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
    AUDITED_PATHS = ['/api/v1/emissions/', '/api/v1/ingestion/', '/api/v1/audit/']

    def process_request(self, request):
        request._audit_start_time = time.time()

    def process_response(self, request, response):
        if request.method in self.AUDITED_METHODS:
            if any(request.path.startswith(p) for p in self.AUDITED_PATHS):
                duration = time.time() - getattr(request, '_audit_start_time', time.time())
                logger.info(
                    f"AUDIT | {request.method} {request.path} | "
                    f"Status: {response.status_code} | "
                    f"User: {getattr(request.user, 'email', 'anonymous')} | "
                    f"Tenant: {getattr(getattr(request, 'tenant', None), 'slug', 'none')} | "
                    f"Duration: {duration:.3f}s"
                )
        return response
