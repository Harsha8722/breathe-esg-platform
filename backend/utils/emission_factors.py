"""
GHG emission factors for common activity types.
Based on GHG Protocol 2023 and EPA emission factors.
All factors in kgCO2e per canonical unit.
"""
from decimal import Decimal

# Fuel emission factors (kgCO2e per liter)
FUEL_FACTORS_PER_LITER = {
    'diesel': Decimal('2.6879'),
    'gasoline': Decimal('2.3120'),
    'petrol': Decimal('2.3120'),
    'natural_gas_liquid': Decimal('1.5422'),
    'jet_fuel': Decimal('2.5401'),
    'kerosene': Decimal('2.5401'),
    'lpg': Decimal('1.5095'),
    'fuel_oil': Decimal('2.9526'),
    'heating_oil': Decimal('2.6827'),
}

# Fuel factors per kg
FUEL_FACTORS_PER_KG = {
    'coal': Decimal('2.4200'),
    'natural_gas': Decimal('2.2030'),  # per kg
    'wood': Decimal('0.0150'),
}

# Fuel factors per kWh (energy content)
FUEL_FACTORS_PER_KWH = {
    'natural_gas': Decimal('0.2032'),
    'lpg': Decimal('0.2149'),
    'diesel': Decimal('0.2668'),
    'coal': Decimal('0.3414'),
}

# Electricity emission factors (kgCO2e per kWh) by region
ELECTRICITY_FACTORS = {
    'us': Decimal('0.3860'),
    'us_avg': Decimal('0.3860'),
    'uk': Decimal('0.2312'),
    'eu': Decimal('0.2760'),
    'in': Decimal('0.7082'),
    'cn': Decimal('0.5810'),
    'au': Decimal('0.6900'),
    'global_avg': Decimal('0.4750'),
    'default': Decimal('0.4750'),
}

# Travel emission factors (kgCO2e per passenger-km)
TRAVEL_FACTORS_PER_PKM = {
    'flight_short_haul': Decimal('0.2551'),   # < 3700 km
    'flight_long_haul': Decimal('0.1950'),    # >= 3700 km
    'flight_domestic': Decimal('0.2552'),
    'flight_economy': Decimal('0.1950'),
    'flight_business': Decimal('0.5590'),
    'flight_first': Decimal('0.8580'),
    'rail': Decimal('0.0410'),
    'rail_eurostar': Decimal('0.0060'),
    'bus': Decimal('0.0897'),
    'taxi': Decimal('0.1490'),
    'car_rental': Decimal('0.1710'),
    'hotel_night': Decimal('20.6'),  # kgCO2e per room night
    'hotel': Decimal('20.6'),
}


def get_fuel_factor(fuel_type: str, unit_type: str = 'volume_fuel') -> tuple:
    """Returns (emission_factor, source_description)"""
    fuel_key = fuel_type.lower().replace(' ', '_').replace('-', '_')

    if unit_type == 'volume_fuel':
        factor = FUEL_FACTORS_PER_LITER.get(fuel_key)
        if factor:
            return factor, f'GHG Protocol 2023 - {fuel_key} per liter'

    if unit_type == 'mass':
        factor = FUEL_FACTORS_PER_KG.get(fuel_key)
        if factor:
            return factor, f'GHG Protocol 2023 - {fuel_key} per kg'

    if unit_type == 'energy':
        factor = FUEL_FACTORS_PER_KWH.get(fuel_key)
        if factor:
            return factor, f'GHG Protocol 2023 - {fuel_key} per kWh'

    # Fallback: try fuzzy match
    for key, val in FUEL_FACTORS_PER_LITER.items():
        if key in fuel_key or fuel_key in key:
            return val, f'GHG Protocol 2023 (approx) - {key} per liter'

    return Decimal('0'), 'Unknown fuel type - factor not applied'


def get_electricity_factor(region: str = 'default') -> tuple:
    """Returns (emission_factor, source_description)"""
    region_key = region.lower().strip()
    factor = ELECTRICITY_FACTORS.get(region_key, ELECTRICITY_FACTORS['default'])
    return factor, f'IEA 2023 Grid Emission Factor - {region}'


def get_travel_factor(travel_mode: str, travel_class: str = 'economy') -> tuple:
    """Returns (emission_factor, source_description)"""
    mode_key = travel_mode.lower().replace(' ', '_')
    class_key = travel_class.lower().replace(' ', '_')

    # Check specific mode+class combo
    combo_key = f"{mode_key}_{class_key}"
    factor = TRAVEL_FACTORS_PER_PKM.get(combo_key) or TRAVEL_FACTORS_PER_PKM.get(mode_key)

    if factor:
        return factor, f'GHG Protocol Corporate Value Chain Standard - {mode_key}'
    return Decimal('0.2'), 'GHG Protocol (default travel factor)'
