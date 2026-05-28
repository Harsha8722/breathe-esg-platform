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

from utils.date_parser import parse_date_flexible
from utils.unit_normalizer import convert_quantity
from utils.emission_factors import get_electricity_factor

logger = logging.getLogger(__name__)

# Column aliases for utility electricity exports
UTILITY_COLUMN_ALIASES = {
    'billing_date': [
        'Bill Date', 'Invoice Date', 'Billing Date', 'Period End Date',
        'Service Date', 'Date', 'Statement Date', 'Month', 'Period',
        'Billing Period End', 'Reading Date', 'Service End Date',
    ],
    'meter_id': [
        'Meter ID', 'Meter Number', 'Account Number', 'Account No',
        'Meter Serial', 'Utility Account', 'MPAN', 'Meter_ID',
        'Account ID', 'Site ID', 'Meter Reference',
    ],
    'consumption': [
        'Consumption', 'Usage', 'kWh', 'Energy Used', 'Units',
        'Electricity Used', 'Quantity', 'Amount', 'Net Usage',
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
        'Rate Plan', 'Electric Rate',
    ],
    'supplier': [
        'Supplier', 'Utility', 'Provider', 'Utility Company',
        'Energy Supplier', 'Vendor', 'Utility Provider',
    ],
    'cost': [
        'Cost', 'Amount', 'Total Cost', 'Bill Amount', 'Charge',
        'Total Charges', 'Invoice Amount', 'Total Amount Due',
    ],
    'currency': [
        'Currency', 'CCY', 'Currency Code',
    ],
    'grid_region': [
        'Grid Region', 'Region', 'State', 'Country', 'Grid Zone',
        'Emission Zone', 'Electricity Region', 'Grid',
    ],
}


def map_columns(df: pd.DataFrame) -> dict:
    """Map DataFrame columns to canonical field names using alias lookup."""
    col_map = {}
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for canonical, aliases in UTILITY_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in df_cols_lower:
                col_map[canonical] = df_cols_lower[alias.lower()]
                break
    return col_map


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


class UtilityElectricityParser:
    def __init__(self, source_file_obj):
        self.source_file = source_file_obj
        self.seen_hashes = set()

    def parse(self, file_path: str) -> list:
        """
        Parse a utility electricity export file.
        Returns list of normalized record dicts.
        """
        try:
            fp = str(file_path)
            if fp.endswith('.xlsx') or fp.endswith('.xls'):
                df = pd.read_excel(fp, dtype=str)
            else:
                for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        df = pd.read_csv(fp, dtype=str, encoding=encoding, sep=None, engine='python')
                        break
                    except Exception:
                        continue
                else:
                    raise ValueError("Could not read file with any known encoding")
        except Exception as e:
            logger.error(f"Failed to read utility electricity file: {e}")
            raise ValueError(f"Cannot read file: {e}")

        col_map = map_columns(df)
        logger.info(f"UtilityElectricityParser: Detected column mapping: {col_map}")

        records = []
        for idx, row in df.iterrows():
            result = self._parse_row(row, idx + 2, col_map)
            if result:
                records.append(result)

        return records

    def _parse_row(self, row: pd.Series, row_number: int, col_map: dict) -> dict:
        """Parse a single utility row into a normalized record dict."""
        original = row.to_dict()
        errors = []
        suspicious_reasons = []

        def get(field):
            col = col_map.get(field)
            if col and col in row.index:
                val = row[col]
                return None if pd.isna(val) else str(val).strip()
            return None

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
        if raw_qty in (None, '', 'nan'):
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
