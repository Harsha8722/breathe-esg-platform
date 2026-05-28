"""Breathe ESG Platform - URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def api_root(request):
    """Root endpoint - returns API info and health status."""
    return JsonResponse({
        "name": "Breathe ESG Platform API",
        "version": "1.0.0",
        "status": "running",
        "message": "Backend API is healthy. Open http://localhost:3000/ for the frontend.",
        "endpoints": {
            "auth": "/api/v1/auth/",
            "tenants": "/api/v1/tenants/",
            "ingestion": "/api/v1/ingestion/",
            "emissions": "/api/v1/emissions/",
            "audit": "/api/v1/audit/",
            "analytics": "/api/v1/analytics/",
            "admin": "/admin/",
        }
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/tenants/', include('apps.tenants.urls')),
    path('api/v1/ingestion/', include('apps.ingestion.urls')),
    path('api/v1/emissions/', include('apps.emissions.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

