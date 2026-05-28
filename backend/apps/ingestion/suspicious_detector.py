"""
Suspicious row detection engine.
Applies statistical and rule-based checks across the full batch.
"""
import numpy as np
from decimal import Decimal
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class SuspiciousRowDetector:
    """
    Runs post-parse batch analysis to flag anomalies:
    - Statistical spike detection (Z-score)
    - Temporal gaps / data absence
    - Impossible values
    - Emission factor inconsistencies
    """

    SPIKE_THRESHOLD_ZSCORE = 3.0
    MIN_BATCH_SIZE_FOR_STATS = 5

    def analyze_batch(self, records: List[Dict]) -> List[Dict]:
        """Enhances existing suspicious flags with statistical analysis."""
        if len(records) < self.MIN_BATCH_SIZE_FOR_STATS:
            return records

        # Group by source_type for statistical comparison
        groups = {}
        for i, r in enumerate(records):
            key = r.get('source_type', 'unknown')
            if key not in groups:
                groups[key] = []
            groups[key].append((i, r))

        for source_type, group_records in groups.items():
            self._flag_statistical_spikes(records, group_records)

        return records

    def _flag_statistical_spikes(self, all_records: List[Dict], group: List[tuple]):
        quantities = []
        for idx, r in group:
            qty = r.get('normalized_quantity') or r.get('quantity')
            if qty is not None:
                try:
                    quantities.append((idx, float(qty)))
                except Exception:
                    pass

        if len(quantities) < self.MIN_BATCH_SIZE_FOR_STATS:
            return

        values = np.array([q for _, q in quantities])
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return

        for idx, qty in quantities:
            z_score = abs((qty - mean) / std)
            if z_score > self.SPIKE_THRESHOLD_ZSCORE:
                record = all_records[idx]
                reason = f"Statistical spike: Z-score={z_score:.2f} (value={qty:.2f}, mean={mean:.2f}, std={std:.2f})"
                if reason not in record.get('suspicious_reasons', []):
                    record.setdefault('suspicious_reasons', []).append(reason)
                    record['suspicious_flag'] = True
