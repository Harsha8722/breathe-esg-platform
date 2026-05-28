"""
Django management command: seed_data
Creates sample tenant, users, and realistic ESG records for demo/testing.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
import random
from datetime import date, timedelta

from apps.tenants.models import Tenant
from apps.authentication.models import User
from apps.emissions.models import EmissionRecord, SourceFile


class Command(BaseCommand):
    help = 'Seeds the database with realistic ESG demo data'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete existing data first')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting demo data...')
            Tenant.objects.filter(slug='acme-corp').delete()

        self.stdout.write('Creating tenant...')
        tenant, _ = Tenant.objects.get_or_create(
            slug='acme-corp',
            defaults={
                'name': 'ACME Corporation',
                'plan': Tenant.Plan.ENTERPRISE,
                'industry': 'Manufacturing',
                'country': 'US',
                'reporting_year': 2024,
            }
        )

        self.stdout.write('Creating users...')
        users_data = [
            {'email': 'admin@breathe.io', 'first_name': 'Alex', 'last_name': 'Chen', 'role': User.Role.ADMIN, 'password': 'Admin@123!'},
            {'email': 'analyst@breathe.io', 'first_name': 'Sarah', 'last_name': 'Martinez', 'role': User.Role.ANALYST, 'password': 'Analyst@123!'},
            {'email': 'reviewer@breathe.io', 'first_name': 'James', 'last_name': 'Okafor', 'role': User.Role.REVIEWER, 'password': 'Review@123!'},
            {'email': 'viewer@breathe.io', 'first_name': 'Priya', 'last_name': 'Sharma', 'role': User.Role.VIEWER, 'password': 'View@123!'},
        ]

        admin_user = None
        for ud in users_data:
            password = ud.pop('password')
            user, created = User.objects.get_or_create(email=ud['email'], defaults={**ud, 'tenant': tenant})
            if created:
                user.set_password(password)
                user.save()
            if ud['email'] == 'admin@breathe.io':
                admin_user = user

        self.stdout.write('Creating source file...')
        sf, _ = SourceFile.objects.get_or_create(
            original_filename='sap_fuel_export_q1_2024.csv',
            tenant=tenant,
            defaults={
                'uploaded_by': admin_user,
                'source_type': SourceFile.SourceType.SAP_FUEL,
                'file_path': 'uploads/2024/01/sap_fuel_export_q1_2024.csv',
                'file_size_bytes': 52400,
                'status': SourceFile.Status.PROCESSED,
                'total_rows': 120,
                'processed_rows': 115,
                'flagged_rows': 8,
                'failed_rows': 5,
                'ingestion_timestamp': timezone.now(),
            }
        )

        self.stdout.write('Creating emission records...')
        records = []
        scopes = ['scope_1', 'scope_2', 'scope_3']
        activities = {
            'scope_1': [('stationary_combustion', 'sap_fuel'), ('mobile_combustion', 'sap_fuel')],
            'scope_2': [('purchased_electricity', 'utility_electricity')],
            'scope_3': [('business_travel', 'corporate_travel'), ('upstream_transport', 'corporate_travel')],
        }
        locations = ['Plant-DE01', 'Plant-US02', 'HQ-NYC', 'Plant-IN03', 'Warehouse-UK']
        vendors = ['Shell Energy', 'BP Fuels', 'National Grid', 'EDF', 'SAP Procurement']
        statuses = [
            EmissionRecord.Status.PENDING, EmissionRecord.Status.PENDING,
            EmissionRecord.Status.FLAGGED, EmissionRecord.Status.APPROVED,
            EmissionRecord.Status.REJECTED, EmissionRecord.Status.LOCKED,
        ]

        base_date = date(2024, 1, 1)
        for i in range(115):
            scope = random.choice(scopes)
            act, src = random.choice(activities[scope])
            qty = Decimal(str(round(random.uniform(10, 5000), 2)))
            ef = Decimal(str(round(random.uniform(0.1, 3.0), 4)))
            st = random.choice(statuses)
            is_suspicious = random.random() < 0.08
            is_dup = random.random() < 0.05

            records.append(EmissionRecord(
                tenant=tenant,
                source_file=sf,
                status=st,
                scope_category=scope,
                activity_category=act,
                source_type=src,
                activity_date=base_date + timedelta(days=random.randint(0, 180)),
                quantity=qty,
                raw_unit=random.choice(['liters', 'kWh', 'km', 'gallons', 'MWh']),
                normalized_unit=random.choice(['liters', 'kWh', 'km']),
                normalized_quantity=qty,
                source_identifier=f"DOC-{random.randint(100000, 999999)}",
                location=random.choice(locations),
                vendor=random.choice(vendors),
                emission_factor=ef,
                emission_factor_source='GHG Protocol 2023',
                calculated_emissions=qty * ef,
                suspicious_flag=is_suspicious,
                suspicious_reasons=['Statistical spike: Z-score=3.4'] if is_suspicious else [],
                validation_errors=['Missing unit'] if random.random() < 0.05 else [],
                is_duplicate=is_dup,
                original_payload={'raw_row': f'sample-row-{i}'},
                row_number=i + 2,
                analyst_notes='Reviewed - source verified' if st == EmissionRecord.Status.APPROVED else '',
                approved_by=admin_user if st in [EmissionRecord.Status.APPROVED, EmissionRecord.Status.LOCKED] else None,
                approved_at=timezone.now() if st in [EmissionRecord.Status.APPROVED, EmissionRecord.Status.LOCKED] else None,
            ))

        EmissionRecord.objects.bulk_create(records, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f'\nSeed complete!\n'
            f'   Tenant: {tenant.name}\n'
            f'   Users: admin@breathe.io / analyst@breathe.io / reviewer@breathe.io\n'
            f'   Password: Admin@123! / Analyst@123! / Review@123!\n'
            f'   Records created: {len(records)}\n'
        ))
