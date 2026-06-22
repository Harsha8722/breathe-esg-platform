"""
JSON sanitization utilities for PostgreSQL JSONField compatibility.

Recursively converts pandas/numpy/decimal types that are not valid JSON
into safe Python natives before persisting to PostgreSQL JSONField columns.

PostgreSQL's JSON type rejects:
  - NaN (numpy.nan, float('nan'), pd.NA, pd.NaT)
  - Infinity / -Infinity
  - numpy int64/float64 (not native Python types)
  - Decimal (not JSON-serializable)
  - datetime objects (must be ISO strings)

This module provides a single entry point: sanitize_for_json()
"""
import math
import datetime
from decimal import Decimal

import numpy as np
import pandas as pd

import logging

logger = logging.getLogger(__name__)


def sanitize_for_json(obj):
    """
    Recursively clean a Python object so it contains only valid JSON types.

    Handles:
        NaN / numpy.nan / float('nan')   → None
        pd.NA / pd.NaT                   → None
        numpy.int64 / numpy.int32 / ...  → int
        numpy.float64 / numpy.float32    → float (or None if NaN/Inf)
        numpy.bool_                      → bool
        numpy.ndarray                    → list (recursively cleaned)
        Decimal                          → float (or None if NaN/Inf)
        datetime.date / datetime.datetime→ ISO 8601 string
        Infinity / -Infinity             → None
        dict                             → recursively cleaned dict
        list / tuple                     → recursively cleaned list
        str / int / float / bool / None  → passed through (float checked for NaN/Inf)
    """
    return _sanitize(obj)


def _sanitize(obj):
    # ---- None / pd.NA / pd.NaT ----
    if obj is None:
        return None

    if isinstance(obj, type(pd.NA)):
        return None

    if isinstance(obj, type(pd.NaT)):
        return None

    # pd.NaT is a singleton; also catch via identity
    try:
        if obj is pd.NaT or obj is pd.NA:
            return None
    except Exception:
        pass

    # ---- numpy scalar types ----
    if isinstance(obj, (np.integer,)):
        return int(obj)

    if isinstance(obj, (np.floating,)):
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val

    if isinstance(obj, (np.bool_,)):
        return bool(obj)

    if isinstance(obj, np.ndarray):
        return [_sanitize(item) for item in obj.tolist()]

    # ---- Python float (may be NaN / Inf) ----
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    # ---- Decimal ----
    if isinstance(obj, Decimal):
        try:
            val = float(obj)
            if math.isnan(val) or math.isinf(val):
                return None
            return val
        except Exception:
            return None

    # ---- Date / Datetime ----
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

    if isinstance(obj, datetime.date):
        return obj.isoformat()

    # ---- Containers (recursive) ----
    if isinstance(obj, dict):
        return {_sanitize(k): _sanitize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_sanitize(item) for item in obj]

    # ---- Primitives: str, int, bool ----
    if isinstance(obj, (str, int, bool)):
        return obj

    # ---- Fallback: convert to string ----
    try:
        return str(obj)
    except Exception:
        return None
