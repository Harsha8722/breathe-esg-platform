"""
Utility Electricity ingestion parser.
Handles utility bill exports (CSV/Excel) for Scope 2 electricity.
Supports various utility formats with column alias resolution, unit normalization,
duplicate detection, and emission factor lookup.
"""
import pandas as pd
from decimal import Decimal
import hashlib
import logging

from apps.ingestion.parsers.base_parser import BaseParser
from utils.date_parser import parse_date_flexible
from utils.emission_factors import get_electricity_factor

logger = logging.getLogger(__name__)

# Column aliases for utility electricity exports
UTILITY_COLUMN_ALIASES = {
    'billing_date': [
        'Bill Date', 'Invoice Date', 'Billing Date', 'Period End Date',
        'Service Date', 'Date', 'Statement Date', 'Month', 'Period',
        'Billing Period End', 'Reading Date', 'Service End Date',
        'Billing Start', 'Billing End',
    ],
    'meter_id': [
        'Meter ID', 'Meter Number', 'Account Number', 'Account No',
        'Meter Serial', 'Utility Account', 'MPAN', 'Meter_ID',
        'Account ID', 'Site ID', 'Meter Reference',
    ],
    'consumption': [
        'Consumption', 'Usage', 'kWh', 'Energy Used', 'Usage (kWh)',
        'Electricity Used', 'Quantity', 'Net Usage',
        'Total Consumption', 'Billable Usage', 'Energy Consumption',
        'MWh', 'GWh',
    ],
    'unit': [
        'Unit', 'UOM', 'Units', 'Unit of Measure', 'Measure',
        'Consumption Unit', 'Usage Unit',
    ],
    'location': [
        'Location', 'Site', 'Address', 'Building', 'Facility',
        'Site Name', 'Premise', 'Service Address', 'Property',
    ],
    'tariff': [
        'Tariff', 'Rate', 'Plan', 'Rate Code', 'Tariff Code',
        'Rate Plan', 'Electric Rate', 'Tariff Type',
    ],
    'supplier': [
        'Supplier', 'Utility', 'Provider', 'Utility Company',
        'Energy Supplier', 'Vendor', 'Utility Provider',
        'Account Name',
    ],
    'cost': [
        'Cost', 'Total Cost', 'Bill Amount', 'Charge',
        'Total Charges', 'Invoice Amount', 'Total Amount Due',
        'Total Charge',
    ],
    'currency': [
        'Currency', 'CCY', 'Currency Code',
    ],
    'grid_region': [
        'Grid Region', 'Region', 'State', 'Country', 'Grid Zone',
        'Emission Zone', 'Electricity Region', 'Grid',
    ],
}


def compute_row_hash(row_data: dict) -> str:
    """Generate a deterministic hash for duplicate detection."""
    key = '|'.join([
        str(row_data.get('billing_date', '')),
        str(row_data.get('meter_id', '')),
        str(row_data.get('consumption', '')),
        str(row_data.get('unit', '')),
        str(row_data.get('location', '')),
    ])
    return hashlib.md5(key.encode()).hexdigest()


def normalize_unit(raw_unit: str) -> str:
    """Normalize electricity unit to kWh equivalent string."""
    if not raw_unit:
        return 'kWh'
    u = raw_unit.lower().strip()
    if u in ('mwh', 'megawatt hour', 'megawatt-hour'):
        return 'MWh'
    if u in ('gwh', 'gigawatt hour', 'gigawatt-hour'):
        return 'GWh'
    return 'kWh'


class UtilityElectricityParser(BaseParser):
    PARSER_NAME = 'UtilityElectricityParser'
    COLUMN_ALIASES = UTILITY_COLUMN_ALIASES
    REQUIRED_COLUMNS = ['billing_date', 'consumption']

    def __init__(self, source_file_obj):
        super().__init__(source_file_obj)
        self.seen_hashes = set()

    def _parse_row(self, row: pd.Series, row_number: int, col_map: dict) -> dict:
        """Parse a single utility row into a normalized record dict."""
        original = row.to_dict()
        errors = []
        suspicious_reasons = []

        get = lambda field: self._get_field(row, col_map, field)

        # Parse billing date
        raw_date = get('billing_date')
        activity_date, date_err = parse_date_flexible(raw_date)
        if date_err:
            errors.append(f"Date: {date_err}")

        # Parse meter/account ID
        meter_id = get('meter_id') or ''

        # Parse consumption
        raw_qty = get('consumption')
        quantity = None
        if raw_qty is None or raw_qty == '':
            errors.append("Missing consumption quantity")
        else:
            try:
                quantity = Decimal(str(raw_qty).replace(',', '.').replace(' ', ''))
            except Exception:
                errors.append(f"Invalid consumption value: '{raw_qty}'")

        # Parse unit
        raw_unit = get('unit') or 'kWh'
        normalized_unit = normalize_unit(raw_unit)

        # Convert to kWh if needed
        normalized_qty = quantity
        if normalized_unit == 'MWh' and quantity is not None:
            normalized_qty = quantity * Decimal('1000')
            normalized_unit = 'kWh'
        elif normalized_unit == 'GWh' and quantity is not None:
            normalized_qty = quantity * Decimal('1000000')
            normalized_unit = 'kWh'

        # Other fields
        location = get('location') or ''
        grid_region = get('grid_region') or ''
        supplier = get('supplier') or ''
        tariff = get('tariff') or ''

        # Emission factor lookup (use grid_region or country)
        region_key = grid_region or location or 'US'
        emission_factor, ef_source = get_electricity_factor(region_key)
        calculated_emissions = None
        if normalized_qty is not None and emission_factor:
            calculated_emissions = normalized_qty * emission_factor

        # Suspicious checks
        if quantity is not None and quantity <= 0:
            suspicious_reasons.append('Non-positive consumption')
        if normalized_qty is not None and normalized_qty > 10_000_000:
            suspicious_reasons.append('Unusually high electricity consumption (>10 GWh equivalent)')
        if activity_date and activity_date.year < 2015:
            suspicious_reasons.append('Date appears too old (pre-2015)')
        if not meter_id:
            suspicious_reasons.append('Missing meter/account identifier')

        # Duplicate detection
        row_hash = compute_row_hash({
            'billing_date': activity_date,
            'meter_id': meter_id,
            'consumption': quantity,
            'unit': raw_unit,
            'location': location,
        })
        is_duplicate = row_hash in self.seen_hashes
        if is_duplicate:
            suspicious_reasons.append('Potential duplicate bill (same date/meter/consumption/location)')
        else:
            self.seen_hashes.add(row_hash)

        return {
            'source_type': 'utility_electricity',
            'scope_category': 'scope_2',
            'activity_category': 'purchased_electricity',
            'activity_date': activity_date,
            'quantity': quantity,
            'raw_unit': raw_unit,
            'normalized_unit': 'kWh',
            'normalized_quantity': normalized_qty,
            'source_identifier': meter_id,
            'location': location,
            'cost_center': '',
            'vendor': supplier,
            'emission_factor': emission_factor,
            'emission_factor_source': ef_source,
            'calculated_emissions': calculated_emissions,
            'validation_errors': errors,
            'suspicious_flag': bool(suspicious_reasons),
            'suspicious_reasons': suspicious_reasons,
            'is_duplicate': is_duplicate,
            'original_payload': original,
            'row_number': row_number,
        }
