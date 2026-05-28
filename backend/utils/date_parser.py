"""
Date parsing utilities to handle malformed/multilingual date formats.
"""
from datetime import date, datetime
import re
from dateutil import parser as dateutil_parser

# Common malformed/locale date patterns
DATE_PATTERNS = [
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%m/%d/%Y',
    '%d-%m-%Y',
    '%m-%d-%Y',
    '%Y%m%d',
    '%d.%m.%Y',
    '%m.%d.%Y',
    '%d %b %Y',
    '%d %B %Y',
    '%b %d, %Y',
    '%B %d, %Y',
    '%Y/%m/%d',
    '%d/%m/%y',
    '%m/%d/%y',
]

# SAP-style date handling: sometimes dates come as Excel serial numbers
EXCEL_EPOCH = datetime(1899, 12, 30)


def parse_date_flexible(raw_value) -> tuple:
    """
    Attempts to parse a date from various formats.
    Returns (parsed_date: date | None, error: str | None)
    """
    if raw_value is None or str(raw_value).strip() in ('', 'nan', 'NaT', 'None', 'N/A', '-'):
        return None, 'Missing date value'

    raw_str = str(raw_value).strip()

    # Handle Excel serial number dates
    if re.match(r'^\d{5}$', raw_str):
        try:
            delta = int(raw_str)
            parsed = EXCEL_EPOCH + __import__('datetime').timedelta(days=delta)
            return parsed.date(), None
        except Exception:
            pass

    # Try structured formats first
    for fmt in DATE_PATTERNS:
        try:
            return datetime.strptime(raw_str, fmt).date(), None
        except ValueError:
            continue

    # Fallback: dateutil fuzzy parse
    try:
        return dateutil_parser.parse(raw_str, fuzzy=True).date(), None
    except Exception:
        return None, f"Cannot parse date: '{raw_str}'"


def is_date_in_future(d: date) -> bool:
    return d is not None and d > date.today()


def is_date_too_old(d: date, years: int = 10) -> bool:
    if d is None:
        return False
    return (date.today() - d).days > years * 365
