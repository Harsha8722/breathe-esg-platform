"""
Corporate travel ingestion parser (Concur/Navan-style exports).
Handles: flights, hotels, rail, taxi with airport codes, distance estimation.
"""
import pandas as pd
from decimal import Decimal
import logging

from utils.date_parser import parse_date_flexible
from utils.emission_factors import get_travel_factor

logger = logging.getLogger(__name__)

TRAVEL_COLUMN_ALIASES = {
    'travel_date': ['Travel Date', 'Trip Date', 'Departure Date', 'Date', 'Service Date', 'Transaction Date'],
    'expense_type': ['Expense Type', 'Category', 'Travel Type', 'Mode', 'Type', 'Expense Category'],
    'origin': ['From', 'Origin', 'Departure', 'From City', 'Origin Airport', 'Departure Airport', 'Start Location'],
    'destination': ['To', 'Destination', 'Arrival', 'To City', 'Destination Airport', 'Arrival Airport', 'End Location'],
    'distance_km': ['Distance (km)', 'Distance', 'Km', 'Miles', 'KM', 'Trip Distance', 'Distance_km'],
    'traveler': ['Employee', 'Traveler', 'Name', 'Employee Name', 'Traveler Name', 'Employee ID'],
    'amount': ['Amount', 'Cost', 'Total Cost', 'Expense Amount', 'Price', 'Fare'],
    'currency': ['Currency', 'CCY', 'Currency Code'],
    'travel_class': ['Class', 'Cabin Class', 'Travel Class', 'Seat Class', 'Booking Class'],
    'vendor': ['Vendor', 'Airline', 'Hotel', 'Carrier', 'Provider', 'Supplier'],
    'nights': ['Nights', 'Duration (nights)', 'Hotel Nights', 'Num Nights'],
    'passengers': ['Passengers', 'Pax', 'Number of Travelers', 'Headcount'],
}

TRAVEL_MODE_MAP = {
    'air': 'flight', 'flight': 'flight', 'airline': 'flight', 'plane': 'flight',
    'domestic flight': 'flight_domestic', 'international flight': 'flight_long_haul',
    'rail': 'rail', 'train': 'rail', 'eurostar': 'rail_eurostar',
    'hotel': 'hotel', 'accommodation': 'hotel', 'lodging': 'hotel',
    'taxi': 'taxi', 'cab': 'taxi', 'uber': 'taxi', 'rideshare': 'taxi',
    'car': 'car_rental', 'rental car': 'car_rental', 'car hire': 'car_rental',
    'bus': 'bus', 'coach': 'bus',
}

# Approximate flight distances for common route pairs (km)
AIRPORT_DISTANCES = {
    ('JFK', 'LHR'): 5571, ('LHR', 'JFK'): 5571,
    ('LAX', 'LHR'): 8757, ('LHR', 'LAX'): 8757,
    ('JFK', 'CDG'): 5839, ('CDG', 'JFK'): 5839,
    ('SFO', 'NRT'): 8285, ('NRT', 'SFO'): 8285,
    ('BOM', 'LHR'): 7191, ('LHR', 'BOM'): 7191,
    ('SIN', 'LHR'): 10841, ('LHR', 'SIN'): 10841,
    ('DXB', 'LHR'): 5484, ('LHR', 'DXB'): 5484,
    ('ORD', 'LHR'): 6349, ('LHR', 'ORD'): 6349,
}


def normalize_travel_mode(raw: str) -> str:
    if not raw:
        return 'unknown'
    lower = raw.lower().strip()
    for key, val in TRAVEL_MODE_MAP.items():
        if key in lower:
            return val
    return lower.replace(' ', '_')


def estimate_distance(origin: str, destination: str) -> tuple:
    if not origin or not destination:
        return None, 'Missing origin/destination'
    o = origin.upper().strip()[:3]
    d = destination.upper().strip()[:3]
    dist = AIRPORT_DISTANCES.get((o, d))
    if dist:
        return Decimal(str(dist)), None
    return None, f"Distance unknown for route {o}-{d}"


def map_columns(df: pd.DataFrame) -> dict:
    col_map = {}
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    for canonical, aliases in TRAVEL_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in df_cols_lower:
                col_map[canonical] = df_cols_lower[alias.lower()]
                break
    return col_map


class CorporateTravelParser:
    def __init__(self, source_file_obj):
        self.source_file = source_file_obj

    def parse(self, file_path: str) -> list:
        try:
            if str(file_path).endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path, dtype=str)
            else:
                df = pd.read_csv(file_path, dtype=str, encoding='utf-8', sep=None, engine='python')
        except Exception as e:
            raise ValueError(f"Cannot read travel file: {e}")

        col_map = map_columns(df)
        records = []
        for idx, row in df.iterrows():
            result = self._parse_row(row, idx + 2, col_map)
            if result:
                records.append(result)
        return records

    def _parse_row(self, row: pd.Series, row_number: int, col_map: dict) -> dict:
        original = row.to_dict()
        errors = []
        suspicious_reasons = []

        def get(field):
            col = col_map.get(field)
            if col and col in row.index:
                val = row[col]
                return None if pd.isna(val) else str(val).strip()
            return None

        raw_date = get('travel_date')
        activity_date, date_err = parse_date_flexible(raw_date)
        if date_err:
            errors.append(f"Date: {date_err}")

        travel_mode = normalize_travel_mode(get('expense_type') or '')
        origin = get('origin') or ''
        destination = get('destination') or ''
        travel_class = (get('travel_class') or 'economy').lower()
        traveler = get('traveler') or ''
        vendor = get('vendor') or ''

        # Distance
        raw_dist = get('distance_km')
        distance_km = None
        if raw_dist and raw_dist not in ('', 'nan', 'N/A'):
            try:
                distance_km = Decimal(str(raw_dist).replace(',', '').replace(' ', ''))
            except Exception:
                errors.append(f"Invalid distance: '{raw_dist}'")

        if distance_km is None and travel_mode in ('flight', 'flight_domestic', 'flight_long_haul'):
            distance_km, dist_err = estimate_distance(origin, destination)
            if dist_err:
                suspicious_reasons.append(f"Distance estimated/unknown: {dist_err}")

        # Nights for hotel
        raw_nights = get('nights')
        nights = None
        if raw_nights and raw_nights not in ('', 'nan'):
            try:
                nights = int(float(raw_nights))
            except Exception:
                pass

        # Emission factor and calculation
        emission_factor, ef_source = get_travel_factor(travel_mode, travel_class)
        calculated_emissions = None

        if travel_mode == 'hotel':
            if nights and nights > 0:
                calculated_emissions = emission_factor * Decimal(str(nights))
            else:
                calculated_emissions = emission_factor  # single night
        elif distance_km and emission_factor:
            calculated_emissions = distance_km * emission_factor
        else:
            if not distance_km:
                errors.append("Cannot calculate emissions: missing distance")

        # Validation
        if not travel_mode or travel_mode == 'unknown':
            errors.append("Unknown travel mode/expense type")
        if not origin and not destination and travel_mode not in ('hotel', 'taxi'):
            errors.append("Missing origin and destination")

        # Suspicious
        if distance_km and distance_km > 20000:
            suspicious_reasons.append(f"Unusually high single-trip distance ({distance_km} km)")
        if calculated_emissions and calculated_emissions > 10000:
            suspicious_reasons.append("Very high emissions for single trip")

        return {
            'source_type': 'corporate_travel',
            'scope_category': 'scope_3',
            'activity_category': 'business_travel',
            'activity_date': activity_date,
            'quantity': distance_km,
            'raw_unit': 'km',
            'normalized_unit': 'km',
            'normalized_quantity': distance_km,
            'source_identifier': f"{origin}-{destination}" if origin or destination else traveler,
            'location': f"{origin} → {destination}",
            'vendor': vendor,
            'traveler': traveler,
            'travel_mode': travel_mode,
            'travel_class': travel_class,
            'nights': nights,
            'emission_factor': emission_factor,
            'emission_factor_source': ef_source,
            'calculated_emissions': calculated_emissions,
            'validation_errors': errors,
            'suspicious_flag': bool(suspicious_reasons),
            'suspicious_reasons': suspicious_reasons,
            'is_duplicate': False,
            'original_payload': original,
            'row_number': row_number,
        }
