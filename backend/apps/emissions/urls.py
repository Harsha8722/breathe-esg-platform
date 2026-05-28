"""Emissions URL routes"""
from django.urls import path
from . import views

urlpatterns = [
    path('records/', views.EmissionRecordListView.as_view(), name='emission-list'),
    path('records/<uuid:pk>/', views.EmissionRecordDetailView.as_view(), name='emission-detail'),
    path('records/<uuid:pk>/review/', views.RecordReviewView.as_view(), name='emission-review'),
    path('records/bulk-action/', views.BulkActionView.as_view(), name='emission-bulk'),
    path('summary/', views.EmissionsSummaryView.as_view(), name='emission-summary'),
]
