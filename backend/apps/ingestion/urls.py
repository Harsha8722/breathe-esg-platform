"""Ingestion URL routes"""
from django.urls import path
from . import views

urlpatterns = [
    path('uploads/', views.SourceFileListView.as_view(), name='ingestion-list'),
    path('uploads/upload/', views.SourceFileUploadView.as_view(), name='ingestion-upload'),
    path('uploads/<uuid:pk>/', views.SourceFileDetailView.as_view(), name='ingestion-detail'),
]
