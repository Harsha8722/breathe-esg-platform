"""
Management command: assign_tenant
Creates a default tenant if none exists and assigns a specific user to it.
Intended as a one-time setup command for initial deployment.
"""
from django.core.management.base import BaseCommand
from apps.tenants.models import Tenant
from apps.authentication.models import User


class Command(BaseCommand):
    help = 'Create a default tenant and assign a user to it'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='breath@gmail.com',
            help='Email of the user to assign (default: breath@gmail.com)',
        )
        parser.add_argument(
            '--tenant-name',
            type=str,
            default='Breathe Default Org',
            help='Name for the tenant (default: Breathe Default Org)',
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            default='breathe-default',
            help='Slug for the tenant (default: breathe-default)',
        )

    def handle(self, *args, **options):
        email = options['email']
        tenant_name = options['tenant_name']
        tenant_slug = options['tenant_slug']

        # Step 1: Create or get the tenant
        tenant, created = Tenant.objects.get_or_create(
            slug=tenant_slug,
            defaults={
                'name': tenant_name,
                'plan': Tenant.Plan.PROFESSIONAL,
                'industry': 'Technology',
                'country': 'IN',
                'reporting_year': 2024,
            },
        )
        status = 'Created' if created else 'Already exists'
        self.stdout.write(f'Tenant: {tenant.name} (id={tenant.id}) — {status}')

        # Step 2: Find the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'User with email "{email}" not found.'))
            return

        # Step 3: Assign user to tenant
        if user.tenant_id == tenant.id:
            self.stdout.write(f'User {email} is already assigned to {tenant.name}')
        else:
            user.tenant = tenant
            user.save(update_fields=['tenant'])
            self.stdout.write(self.style.SUCCESS(
                f'User assigned to tenant successfully — {email} → {tenant.name}'
            ))

        # Step 4: Also make the user staff + admin role so they can use all features
        if not user.is_staff:
            user.is_staff = True
            user.role = User.Role.ADMIN
            user.save(update_fields=['is_staff', 'role'])
            self.stdout.write(f'Promoted {email} to staff + admin role')

        # Summary
        self.stdout.write(self.style.SUCCESS('\n--- Summary ---'))
        self.stdout.write(f'  Tenant : {tenant.name} ({tenant.slug})')
        self.stdout.write(f'  User   : {user.email} (role={user.role})')
        self.stdout.write(f'  Tenant ID : {tenant.id}')
        self.stdout.write(self.style.SUCCESS('User assigned to tenant successfully'))
