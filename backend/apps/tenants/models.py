"""
Tenant model for multi-tenancy support.
"""
from django.db import models
import uuid


class Tenant(models.Model):
    class Plan(models.TextChoices):
        STARTER = 'starter', 'Starter'
        PROFESSIONAL = 'professional', 'Professional'
        ENTERPRISE = 'enterprise', 'Enterprise'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    plan = models.CharField(max_length=30, choices=Plan.choices, default=Plan.PROFESSIONAL)
    industry = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    reporting_year = models.IntegerField(default=2024)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Settings
    fiscal_year_start_month = models.IntegerField(default=1)  # January
    default_currency = models.CharField(max_length=3, default='USD')
    emission_factor_version = models.CharField(max_length=50, default='GHG Protocol 2023')

    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.name
