# DECISIONS.md — Engineering Decision Log

## SAP Format Choice

**Decision**: Implemented SAP ECC/S4HANA-style CSV with multilingual column headers.

**Rationale**: SAP is the dominant ERP in Fortune 500 manufacturing and energy companies. Real SAP exports:
- Use internal field names (BUDAT, MATNR, MENGE, MEINS, WERKS)
- Ship with German/French/Spanish headers depending on system locale
- Inconsistently quote numeric fields
- Use both comma and semicolon delimiters

**Implementation**: Built a column alias dictionary with 8 canonical fields × 5-10 aliases each. Used `sep=None, engine='python'` in pandas to auto-detect delimiters.

**Assumption**: SAP exports represent Scope 1 fuel procurement. In real deployments, the mapping rules would be configured per-tenant.

**PM Question**: Should plant-code → facility mapping be user-configurable? Currently hardcoded.

---

## Utility Electricity Format

**Decision**: Modeled after UK smart meter exports (MPAN), US ESPI standard (NMI), and generic billing CSVs.

**Rationale**: There is no universal utility export format. Each utility provider (National Grid, EDF, Con Edison) generates different column names. The column alias approach handles 80% of real-world variants.

**Key edge case handled**: Overlapping billing periods per meter — detected by tracking (meter_id → [(start, end)]) and flagging overlap as suspicious.

**Ignored edge case**: Demand charges, reactive power, TOU peak/off-peak split billing. These require domain-specific tariff models.

---

## Travel Format Choice

**Decision**: Modeled after Concur Expense / Navan (formerly TripActions) CSV exports.

**Rationale**: These are the two dominant T&E platforms in enterprise. Both export similar columnar formats with expense category, origin/destination, amount, currency.

**Key challenge**: Flights often lack distance. Resolution: implemented a lookup table of ~16 common international routes (JFK-LHR, BOM-LHR, etc.). Unknown routes generate a `suspicious_reasons` flag.

**Assumption**: Hotel nights use a per-room-night emission factor (20.6 kgCO2e). In production, this would vary by hotel chain's carbon reporting.

---

## Assumptions Made

1. All monetary values are ignored for emission calculation (cost is metadata only)
2. GHG Protocol 2023 emission factors are static — no tenant-configurable EF tables in v1
3. All timestamps stored in UTC; display conversion is client-side
4. File upload is synchronous for dev (thread-based); production uses Celery
5. Duplicate detection uses row-level hash (date + qty + unit + fuel + plant) — not ML-based

---

## Ignored Edge Cases

1. Multi-currency normalization for financial reporting
2. Supplier-specific emission factors (Scope 3.1 purchased goods)
3. Real-time electricity emissions (marginal vs. average grid factors)
4. Split billing periods spanning fiscal years
5. Retroactive emission factor updates (currently requires full re-ingestion)

---

## PM Questions Worth Raising

1. Should analysts be able to override emission factors per record?
2. Should locked records ever be unlockable? (Currently terminal)
3. Is bulk lock-after-approval needed for period close workflow?
4. Should there be email notifications when records are flagged?
5. What is the SLA for ingestion processing? (Currently synchronous in dev)
