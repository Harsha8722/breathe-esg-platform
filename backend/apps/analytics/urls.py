"""Analytics URL routes"""
from django.urls import path
from .views import ScopeTrendView, SourceTypeBreakdownView, IngestionStatsView

urlpatterns = [
    path('scope-trend/', ScopeTrendView.as_view(), name='analytics-scope-trend'),
    path('source-breakdown/', SourceTypeBreakdownView.as_view(), name='analytics-source-breakdown'),
    path('ingestion-stats/', IngestionStatsView.as_view(), name='analytics-ingestion-stats'),
]
