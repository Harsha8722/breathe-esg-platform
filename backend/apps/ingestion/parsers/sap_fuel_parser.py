"""
SAP Fuel/Procurement ingestion parser.
Handles SAP ECC / S4HANA CSV exports with:
- Multilingual column headers
- Inconsistent fuel units
- Plant codes, cost centers
- Malformed dates
- Duplicate detection
"""
import pandas as pd
import numpy as np
from decimal import Decimal
import re
import hashlib
import logging

from utils.date_parser import parse_date_flexible
from utils.unit_normalizer import convert_quantity
from utils.emission_factors import get_fuel_factor

logger = logging.getLogger(__name__)

# SAP multilingual column header synonyms
SAP_COLUMN_ALIASES = {
    'activity_date': [
        'Posting Date', 'Buchungsdatum', 'Fecha Contable', 'Date comptable',
        'PostDate', 'Posting_Date', 'BUDAT', 'Document Date', 'Belegdatum',
        'Invoice Date', 'Rechnungsdatum', 'Entry Date', 'Document_Date',
    ],
    'quantity': [
        'Quantity', 'Menge', 'Quantité', 'Cantidad', 'Qty', 'Amount',
        'MENGE', 'Invoice Qty', 'Delivered Qty', 'Delivered_Qty', 'QTY',
    ],
    'unit': [
        'Unit', 'Einheit', 'Unité', 'Unidad', 'UOM', 'Unit of Measure',
        'MEINS', 'Base Unit', 'Order Unit', 'Unit_of_Measure', 'UoM',
    ],
    'fuel_type': [
        'Material', 'Material Description', 'Material_Desc', 'Materialbeschreibung',
        'Description matérielle', 'Descripción material', 'MATNR', 'MAKTX',
        'Fuel Type', 'Product', 'Item Description', 'Short Text',
    ],
    'plant_code': [
        'Plant', 'Werk', 'Usine', 'Planta', 'WERKS', 'Plant Code',
        'Site', 'Location Code', 'Facility', 'Plant_Code',
    ],
    'cost_center': [
        'Cost Center', 'Kostenstelle', 'Centre de coût', 'Centro de coste',
        'KOSTL', 'CC', 'Cost_Center', 'CostCenter',
    ],
    'vendor': [
        'Vendor', 'Lieferant', 'Fournisseur', 'Proveedor', 'Supplier',
        'Vendor Name', 'Vendor_Name', 'LIFNR', 'Vendor Number',
    ],
    'document_number': [
        'PO Number', 'Purchase Order', 'EBELN', 'Document Number',
        'Invoice Number', 'Belegnum', 'Doc No', 'Reference',
    ],
}

# Fuel type normalization
FUEL_TYPE_MAP = {
    'diesel': 'diesel',
    'diesel kraftstoff': 'diesel',
    'gas oil': 'diesel',
    'automotive diesel': 'diesel',
    'petrol': 'gasoline',
    'gasoline': 'gasoline',
    'benzin': 'gasoline',
    'essence': 'gasoline',
    'gasolina': 'gasoline',
    'unleaded': 'gasoline',
    'natural gas': 'natural_gas',
    'erdgas': 'natural_gas',
    'gaz naturel': 'natural_gas',
    'gas nat': 'natural_gas',
    'cng': 'natural_gas',
    'lng': 'natural_gas',
    'lpg': 'lpg',
    'flüssiggas': 'lpg',
    'propane': 'lpg',
    'butane': 'lpg',
    'heating oil': 'heating_oil',
    'fuel oil': 'fuel_oil',
    'kerosene': 'kerosene',
    'jet fuel': 'jet_fuel',
    'jet-a': 'jet_fuel',
    'aviation fuel': 'jet_fuel',
}


def normalize_fuel_type(raw: str) -> str:
    if not raw:
        return 'unknown'
    cleaned = raw.lower().strip()
    for key, val in FUEL_TYPE_MAP.items():
        if key in cleaned:
            return val
    return cleaned.replace(' ', '_')


def map_columns(df: pd.DataFrame) -> dict:
    """Map DataFrame columns to canonical field names using alias lookup."""
    col_map = {}
    df_cols_lower = {c.lower().strip(): c for c in df.columns}

    for canonical, aliases in SAP_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in df_cols_lower:
                col_map[canonical] = df_cols_lower[alias.lower()]
                break

    return col_map


def compute_row_hash(row_data: dict) -> str:
    """Generate a deterministic hash for duplicate detection."""
    key = '|'.join([
        str(row_data.get('activity_date', '')),
        str(row_data.get('quantity', '')),
        str(row_data.get('unit', '')),
        str(row_data.get('fuel_type', '')),
        str(row_data.get('plant_code', '')),
    ])
    return hashlib.md5(key.encode()).hexdigest()


class SAPFuelParser:
    def __init__(self, source_file_obj):
        self.source_file = source_file_obj
        self.seen_hashes = set()
        self.results = []
        self.errors = []

    def parse(self, file_path: str) -> list:
        """
        Parse a SAP fuel export file. Returns list of normalized record dicts.
        """
        try:
            df = self._read_file(file_path)
        except Exception as e:
            logger.error(f"Failed to read SAP file: {e}")
            raise ValueError(f"Cannot read file: {e}")

        col_map = map_columns(df)
        logger.info(f"SAP Parser: Detected column mapping: {col_map}")

        records = []
        for idx, row in df.iterrows():
            result = self._parse_row(row, idx + 2, col_map)  # +2 for 1-indexed + header
            if result:
                records.append(result)

        return records

    def _read_file(self, file_path: str) -> pd.DataFrame:
        """Read CSV or Excel file, handling encoding issues."""
        fp = str(file_path)
        if fp.endswith('.xlsx') or fp.endswith('.xls'):
            return pd.read_excel(fp, dtype=str)

        # Try common encodings for SAP exports
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                df = pd.read_csv(fp, dtype=str, encoding=encoding, sep=None, engine='python')
                return df
            except Exception:
                continue
        raise ValueError("Could not read file with any known encoding")

    def _parse_row(self, row: pd.Series, row_number: int, col_map: dict) -> dict:
        """Parse a single SAP row into a normalized record dict."""
        original = row.to_dict()
        errors = []
        suspicious_reasons = []

        def get(field):
            col = col_map.get(field)
            if col and col in row.index:
                val = row[col]
                return None if pd.isna(val) else str(val).strip()
            return None

        # Parse date
        raw_date = get('activity_date')
        activity_date, date_err = parse_date_flexible(raw_date)
        if date_err:
            errors.append(f"Date: {date_err}")

        # Parse quantity
        raw_qty = get('quantity')
        try:
            if raw_qty in (None, '', 'nan'):
                quantity = None
                errors.append("Missing quantity")
            else:
                quantity = Decimal(str(raw_qty).replace(',', '.').replace(' ', ''))
        except Exception:
            quantity = None
            errors.append(f"Invalid quantity: '{raw_qty}'")

        # Parse unit
        raw_unit = get('unit') or ''

        # Normalize unit
        normalized_qty = None
        normalized_unit = raw_unit
        unit_type = 'unknown'
        try:
            if quantity is not None and raw_unit:
                normalized_qty, normalized_unit, unit_type = convert_quantity(quantity, raw_unit)
        except ValueError as e:
            errors.append(str(e))

        # Fuel type
        raw_fuel = get('fuel_type') or ''
        fuel_type = normalize_fuel_type(raw_fuel)

        # Other fields
        plant_code = get('plant_code') or ''
        cost_center = get('cost_center') or ''
        vendor = get('vendor') or ''
        document_number = get('document_number') or ''

        # Emission factor
        emission_factor, ef_source = get_fuel_factor(fuel_type, unit_type)
        calculated_emissions = None
        if normalized_qty is not None and emission_factor:
            calculated_emissions = normalized_qty * emission_factor

        # Suspicious checks
        if quantity is not None and quantity <= 0:
            suspicious_reasons.append('Non-positive quantity')
        if quantity is not None and quantity > 100000:
            suspicious_reasons.append('Unusually high quantity (>100,000 units)')
        if not raw_unit:
            suspicious_reasons.append('Missing unit of measure')
        if activity_date and activity_date.year < 2018:
            suspicious_reasons.append('Date appears too old')

        # Duplicate detection
        row_hash = compute_row_hash({
            'activity_date': activity_date,
            'quantity': quantity,
            'unit': raw_unit,
            'fuel_type': fuel_type,
            'plant_code': plant_code,
        })
        is_duplicate = row_hash in self.seen_hashes
        if is_duplicate:
            suspicious_reasons.append('Potential duplicate row (same date/qty/unit/fuel/plant)')
        else:
            self.seen_hashes.add(row_hash)

        return {
            'source_type': 'sap_fuel',
            'scope_category': 'scope_1',
            'activity_category': 'stationary_combustion' if fuel_type not in ('jet_fuel',) else 'mobile_combustion',
            'activity_date': activity_date,
            'quantity': quantity,
            'raw_unit': raw_unit,
            'normalized_unit': normalized_unit,
            'normalized_quantity': normalized_qty,
            'source_identifier': document_number or f"PLANT-{plant_code}",
            'location': plant_code,
            'cost_center': cost_center,
            'vendor': vendor,
            'fuel_type': fuel_type,
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
