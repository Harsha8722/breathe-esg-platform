"""Tenants views and serializers"""
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.tenants.models import Tenant
from apps.authentication.models import User
from apps.authentication.serializers import UserSerializer


class TenantSerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'plan', 'industry', 'country',
            'reporting_year', 'is_active', 'fiscal_year_start_month',
            'default_currency', 'emission_factor_version', 'user_count', 'created_at',
        ]

    def get_user_count(self, obj):
        return obj.users.filter(is_active=True).count()


class TenantDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = TenantSerializer

    def get_object(self):
        return self.request.tenant

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response({'success': True, 'data': serializer.data})

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'data': serializer.data})


class TenantUsersView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(tenant=self.request.tenant, is_active=True)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        return Response({'success': True, 'data': self.get_serializer(qs, many=True).data})
