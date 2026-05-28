"""Tenants URL routes"""
from django.urls import path
from .views import TenantDetailView, TenantUsersView

urlpatterns = [
    path('me/', TenantDetailView.as_view(), name='tenant-detail'),
    path('me/users/', TenantUsersView.as_view(), name='tenant-users'),
]
