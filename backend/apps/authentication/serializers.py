"""
Authentication serializers - login, register, token refresh, user profile.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from apps.authentication.models import User
from apps.tenants.models import Tenant


class TenantBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'plan', 'industry']


class UserSerializer(serializers.ModelSerializer):
    tenant = TenantBasicSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'tenant', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_full_name(self, obj):
        return obj.full_name


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['tenant_id'] = str(user.tenant_id) if user.tenant_id else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = UserSerializer(user).data
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    tenant_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'confirm_password', 'role', 'tenant_id']

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        tenant_id = validated_data.pop('tenant_id', None)
        user = User.objects.create_user(**validated_data)
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                user.tenant = tenant
                user.save(update_fields=['tenant'])
            except Tenant.DoesNotExist:
                pass
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
