"""
Abstract base parser for ESG file ingestion.

Provides shared functionality for all concrete parsers:
  - File reading (CSV / Excel) with encoding fallback
  - Header normalization (strip, lowercase, collapse whitespace, remove
    hidden characters like BOM, NBSP, zero-width chars)
  - Alias-based column mapping with normalized comparison
  - Required-column validation with clear error messages
  - Comprehensive logging
"""
import abc
import re
import logging

import pandas as pd

from utils.json_sanitizer import sanitize_for_json

logger = logging.getLogger(__name__)

# Characters to strip from Excel headers that are invisible but break matching
_INVISIBLE_CHARS_RE = re.compile(
    r'[\u200b\u200c\u200d\u200e\u200f'   # zero-width chars
    r'\ufeff'                              # BOM
    r'\u00a0'                              # non-breaking space
    r'\u2002\u2003\u2004\u2005\u2006'      # en/em/various spaces
    r'\u2007\u2008\u2009\u200a'            # figure/punctuation/thin/hair space
    r'\u202f\u205f\u3000'                  # narrow NBSP, medium math, ideographic
    r'\r\n\t]',                            # control whitespace
    re.UNICODE,
)


def normalize_header(header: str) -> str:
    """
    Normalize a column header for comparison.

    Steps:
      1. Remove invisible / special Unicode characters
      2. Collapse all whitespace to a single space
      3. Strip leading/trailing whitespace
      4. Lowercase
      5. Replace underscores with spaces (so Employee_Name == Employee Name)

    Example:
        '  Employee_Name  '  → 'employee name'
        '\\ufeffPosting Date' → 'posting date'
        'EMPLOYEE NAME'      → 'employee name'
    """
    if not isinstance(header, str):
        header = str(header)
    # Strip invisible chars
    header = _INVISIBLE_CHARS_RE.sub(' ', header)
    # Replace underscores with spaces
    header = header.replace('_', ' ')
    # Collapse whitespace
    header = re.sub(r'\s+', ' ', header).strip()
    # Lowercase
    return header.lower()


def map_columns(df: pd.DataFrame, alias_table: dict) -> dict:
    """
    Map DataFrame columns to canonical field names using an alias table.

    Both the DataFrame column names and the alias values are normalized
    before comparison, so 'Employee_Name', 'employee name', 'EMPLOYEE NAME',
    and '\\ufeffEmployee Name' all match the alias 'Employee Name'.

    Args:
        df: The DataFrame whose columns to map.
        alias_table: dict mapping canonical_name → list of alias strings.

    Returns:
        dict mapping canonical_name → original DataFrame column name.
    """
    # Build a lookup: normalized_header → original column name
    # If two columns normalize to the same key, first wins
    col_lookup = {}
    for original_col in df.columns:
        norm = normalize_header(original_col)
        if norm not in col_lookup:
            col_lookup[norm] = original_col

    col_map = {}
    for canonical, aliases in alias_table.items():
        for alias in aliases:
            norm_alias = normalize_header(alias)
            if norm_alias in col_lookup:
                col_map[canonical] = col_lookup[norm_alias]
                break

    return col_map


def read_file(file_path: str) -> pd.DataFrame:
    """
    Read a CSV or Excel file into a DataFrame, all columns as strings.

    For CSV files, tries multiple encodings (utf-8-sig to handle BOM,
    latin-1, cp1252, iso-8859-1) with automatic delimiter detection.

    For Excel files, reads with openpyxl/xlrd via pandas.

    Raises ValueError if the file cannot be read.
    """
    fp = str(file_path)

    if fp.lower().endswith(('.xlsx', '.xls')):
        try:
            return pd.read_excel(fp, dtype=str)
        except Exception as e:
            raise ValueError(f"Cannot read Excel file: {e}")

    # CSV: try encodings in order
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            df = pd.read_csv(fp, dtype=str, encoding=encoding, sep=None, engine='python')
            return df
        except Exception:
            continue

    raise ValueError("Could not read CSV file with any known encoding")


class BaseParser(abc.ABC):
    """
    Abstract base class for ESG file parsers.

    Subclasses must define:
        PARSER_NAME:       str — human-readable parser name for logging
        COLUMN_ALIASES:    dict — canonical_name → list of alias strings
        REQUIRED_COLUMNS:  list — canonical column names that must be present

    Subclasses must implement:
        _parse_row(row, row_number, col_map) → dict | None
    """

    PARSER_NAME: str = 'BaseParser'
    COLUMN_ALIASES: dict = {}
    REQUIRED_COLUMNS: list = []

    def __init__(self, source_file_obj):
        self.source_file = source_file_obj

    def parse(self, file_path: str) -> list:
        """
        Parse a file and return a list of normalized record dicts.

        Steps:
          1. Read file into DataFrame
          2. Normalize headers and map columns
          3. Validate required columns are present
          4. Iterate rows, calling _parse_row for each
          5. Log summary statistics
        """
        parser_name = self.PARSER_NAME

        # Step 1: Read
        logger.info(f"[{parser_name}] Reading file: {file_path}")
        try:
            df = read_file(file_path)
        except Exception as e:
            logger.error(f"[{parser_name}] Failed to read file: {e}")
            raise ValueError(f"Cannot read file: {e}")

        # Step 2: Map columns
        original_headers = list(df.columns)
        normalized_headers = [normalize_header(h) for h in original_headers]
        logger.info(f"[{parser_name}] Original headers: {original_headers}")
        logger.info(f"[{parser_name}] Normalized headers: {normalized_headers}")

        col_map = map_columns(df, self.COLUMN_ALIASES)
        logger.info(f"[{parser_name}] Detected column mapping: {col_map}")

        # Save mapping metadata on the source file
        try:
            self.source_file.detected_columns = sanitize_for_json(original_headers)
            self.source_file.column_mapping_used = sanitize_for_json(col_map)
            self.source_file.save(update_fields=['detected_columns', 'column_mapping_used'])
        except Exception as e:
            logger.warning(f"[{parser_name}] Could not save column metadata: {e}")

        # Step 3: Validate required columns
        missing = [c for c in self.REQUIRED_COLUMNS if c not in col_map]
        if missing:
            msg = (
                f"[{parser_name}] Missing required columns: {missing}. "
                f"Detected mapping has: {list(col_map.keys())}. "
                f"File headers: {original_headers}"
            )
            logger.error(msg)
            raise ValueError(
                f"Missing required columns for {parser_name}: {missing}. "
                f"Found headers: {original_headers}. "
                f"Please check the file format and ensure the correct source type is selected."
            )

        # Step 4: Parse rows
        records = []
        skipped = 0
        failed = 0
        for idx, row in df.iterrows():
            try:
                result = self._parse_row(row, idx + 2, col_map)  # +2: 1-indexed + header
                if result:
                    # Sanitize the original_payload and all JSON-bound fields
                    result['original_payload'] = sanitize_for_json(
                        result.get('original_payload', {})
                    )
                    result['suspicious_reasons'] = sanitize_for_json(
                        result.get('suspicious_reasons', [])
                    )
                    result['validation_errors'] = sanitize_for_json(
                        result.get('validation_errors', [])
                    )
                    records.append(result)
                else:
                    skipped += 1
            except Exception as e:
                logger.warning(f"[{parser_name}] Row {idx + 2} parse error: {e}")
                failed += 1

        # Step 5: Log summary
        logger.info(
            f"[{parser_name}] Parsing complete: "
            f"total_rows={len(df)}, parsed={len(records)}, "
            f"skipped={skipped}, failed={failed}"
        )

        return records

    @abc.abstractmethod
    def _parse_row(self, row: pd.Series, row_number: int, col_map: dict) -> dict | None:
        """
        Parse a single row into a normalized record dict.

        Args:
            row: pandas Series for one row
            row_number: 1-indexed row number (accounting for header)
            col_map: dict of canonical_name → original column name

        Returns:
            dict with normalized fields, or None to skip the row.
        """
        ...

    @staticmethod
    def _get_field(row: pd.Series, col_map: dict, field: str):
        """
        Safely extract a field value from a row using the column mapping.

        Returns None for missing mappings, unmapped columns, and NaN/NA values.
        Returns stripped string otherwise.
        """
        col = col_map.get(field)
        if col and col in row.index:
            val = row[col]
            if pd.isna(val):
                return None
            s = str(val).strip()
            if s.lower() in ('nan', 'nat', 'none', ''):
                return None
            return s
        return None
