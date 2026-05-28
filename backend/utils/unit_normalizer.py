"""
Unit normalization utilities.
Converts all incoming quantity units to canonical SI/metric units.
"""
from decimal import Decimal
import re

# Canonical unit targets
CANONICAL_UNITS = {
    'energy': 'kWh',
    'volume_fuel': 'liters',
    'mass': 'kg',
    'distance': 'km',
}

# Conversion factors to canonical unit
UNIT_CONVERSIONS = {
    # Volume fuel -> Liters
    'l': Decimal('1'),
    'liter': Decimal('1'),
    'liters': Decimal('1'),
    'litre': Decimal('1'),
    'litres': Decimal('1'),
    'lt': Decimal('1'),
    'gal': Decimal('3.78541'),
    'gallon': Decimal('3.78541'),
    'gallons': Decimal('3.78541'),
    'usgal': Decimal('3.78541'),
    'ukgal': Decimal('4.54609'),
    'impgal': Decimal('4.54609'),
    'm3': Decimal('1000'),
    'cbm': Decimal('1000'),
    'cubic meter': Decimal('1000'),
    'cubic metres': Decimal('1000'),

    # Energy -> kWh
    'kwh': Decimal('1'),
    'mwh': Decimal('1000'),
    'gwh': Decimal('1000000'),
    'twh': Decimal('1000000000'),
    'j': Decimal('0.000000277778'),
    'kj': Decimal('0.000277778'),
    'mj': Decimal('0.277778'),
    'gj': Decimal('277.778'),
    'tj': Decimal('277778'),
    'btu': Decimal('0.000293071'),
    'mmbtu': Decimal('293.071'),
    'therm': Decimal('29.3071'),
    'kcal': Decimal('0.001163'),

    # Mass -> kg
    'kg': Decimal('1'),
    'kilogram': Decimal('1'),
    'kilograms': Decimal('1'),
    'g': Decimal('0.001'),
    'gram': Decimal('0.001'),
    'grams': Decimal('0.001'),
    'mt': Decimal('1000'),
    'tonne': Decimal('1000'),
    'tonnes': Decimal('1000'),
    'ton': Decimal('907.185'),  # US short ton
    'tons': Decimal('907.185'),
    'lb': Decimal('0.453592'),
    'lbs': Decimal('0.453592'),
    'pound': Decimal('0.453592'),
    'pounds': Decimal('0.453592'),

    # Distance -> km
    'km': Decimal('1'),
    'kilometer': Decimal('1'),
    'kilometers': Decimal('1'),
    'kilometre': Decimal('1'),
    'kilometres': Decimal('1'),
    'mi': Decimal('1.60934'),
    'mile': Decimal('1.60934'),
    'miles': Decimal('1.60934'),
    'm': Decimal('0.001'),
    'meter': Decimal('0.001'),
    'meters': Decimal('0.001'),
    'ft': Decimal('0.0003048'),
    'feet': Decimal('0.0003048'),
    'nm': Decimal('1.852'),  # nautical mile
    'nmi': Decimal('1.852'),
}

# Unit type mapping
UNIT_TYPE_MAP = {
    'l': 'volume_fuel', 'liter': 'volume_fuel', 'liters': 'volume_fuel',
    'litre': 'volume_fuel', 'litres': 'volume_fuel', 'lt': 'volume_fuel',
    'gal': 'volume_fuel', 'gallon': 'volume_fuel', 'gallons': 'volume_fuel',
    'm3': 'volume_fuel', 'cbm': 'volume_fuel', 'usgal': 'volume_fuel',
    'kwh': 'energy', 'mwh': 'energy', 'gwh': 'energy', 'twh': 'energy',
    'j': 'energy', 'kj': 'energy', 'mj': 'energy', 'gj': 'energy', 'tj': 'energy',
    'btu': 'energy', 'mmbtu': 'energy', 'therm': 'energy', 'kcal': 'energy',
    'kg': 'mass', 'kilogram': 'mass', 'kilograms': 'mass', 'g': 'mass', 'gram': 'mass',
    'mt': 'mass', 'tonne': 'mass', 'tonnes': 'mass', 'ton': 'mass', 'lb': 'mass', 'lbs': 'mass',
    'km': 'distance', 'kilometer': 'distance', 'kilometers': 'distance',
    'mi': 'distance', 'mile': 'distance', 'miles': 'distance',
    'nm': 'distance', 'nmi': 'distance',
}


def normalize_unit_string(raw_unit: str) -> str:
    """Normalize raw unit string to lowercase canonical key."""
    if not raw_unit:
        return ''
    cleaned = raw_unit.strip().lower()
    cleaned = re.sub(r'[^a-z0-9/]', '', cleaned)
    return cleaned


def convert_quantity(quantity, raw_unit: str):
    """
    Convert a quantity from raw_unit to canonical unit.
    Returns (normalized_quantity, canonical_unit, unit_type) or raises ValueError.
    """
    if quantity is None:
        return None, '', ''

    unit_key = normalize_unit_string(raw_unit)
    if not unit_key:
        return Decimal(str(quantity)), raw_unit, 'unknown'

    factor = UNIT_CONVERSIONS.get(unit_key)
    if factor is None:
        # Try partial match
        for key in UNIT_CONVERSIONS:
            if key in unit_key or unit_key in key:
                factor = UNIT_CONVERSIONS[key]
                unit_key = key
                break

    if factor is None:
        raise ValueError(f"Unknown unit: '{raw_unit}'")

    unit_type = UNIT_TYPE_MAP.get(unit_key, 'unknown')
    canonical_unit = CANONICAL_UNITS.get(unit_type, raw_unit)
    normalized = Decimal(str(quantity)) * factor
    return normalized, canonical_unit, unit_type
