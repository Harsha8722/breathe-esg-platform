# MODEL.md — Data Model Documentation

## Multi-Tenancy

Each record in the system belongs to a **Tenant**. The `Tenant` model has:
- UUID primary key (prevents sequential enumeration)
- Plan tier (starter, professional, enterprise)
- Industry and country metadata
- Fiscal year settings
- Emission factor version for regulatory compliance tracking

All API views filter by `request.tenant`, which is resolved from:
1. `X-Tenant-ID` header (for multi-tenant SaaS deployments)
2. JWT claim `tenant_id` (populated at login)

This prevents data leakage between organizations without requiring row-level security at the DB layer.

---

## Canonical Schema: EmissionRecord

The `EmissionRecord` is the normalized, source-of-truth row. It stores:

| Field | Purpose |
|-------|---------|
| `scope_category` | Scope 1/2/3 GHG Protocol classification |
| `activity_category` | Stationary combustion, purchased electricity, etc. |
| `source_type` | sap_fuel, utility_electricity, corporate_travel |
| `quantity` | Raw quantity as extracted |
| `raw_unit` | Original unit from source |
| `normalized_quantity` | Converted to canonical unit |
| `normalized_unit` | liters / kWh / km |
| `emission_factor` | kgCO2e per unit (GHG Protocol 2023) |
| `calculated_emissions` | quantity × emission_factor in kgCO2e |
| `original_payload` | JSON of raw source row (immutable audit copy) |

---

## Normalization Strategy

1. **Column detection**: Fuzzy match column headers against alias dictionaries (SAP multilingual, Concur, utility)
2. **Unit conversion**: Convert all quantities to canonical units (liters, kWh, km) using exact Decimal arithmetic
3. **Date parsing**: Try 15+ date formats + Excel serial numbers + dateutil fuzzy parse
4. **Fuel type normalization**: Map 30+ fuel names to canonical types
5. **Emission calculation**: Apply GHG Protocol / IEA emission factors

---

## Source Tracking

Each `EmissionRecord` links to a `SourceFile`, which records:
- Original filename and upload metadata
- Detected column mapping used
- Processing statistics (total/processed/flagged/failed rows)
- Processing timestamps for SLA tracking

---

## Audit Trail

`AuditLog` entries are created for every significant event:
- File upload
- Ingestion start/complete/fail
- Record approve/reject/flag/lock
- Analyst notes
- Bulk operations

Each entry stores: actor, action, target, before_state, after_state, IP address, timestamp.
**Audit logs are never deleted or modified.**

---

## Approval Lifecycle

```
PENDING → FLAGGED (auto: validation/anomaly failure)
PENDING → APPROVED (analyst: reviewer/admin role required)
PENDING → REJECTED (analyst: reviewer/admin role required)
FLAGGED → APPROVED (after manual review)
FLAGGED → REJECTED (after manual review)
APPROVED → LOCKED (admin only — makes record immutable)
LOCKED → (terminal state)
```

---

## Scope Categorization

| Source | Scope | Rationale |
|--------|-------|-----------|
| SAP Fuel (combustion) | Scope 1 | Direct emissions from owned assets |
| Utility Electricity | Scope 2 | Purchased/indirect energy |
| Corporate Travel | Scope 3 | Value chain / employee activity |

Scope 3 sub-categories (Category 6: Business Travel) follow GHG Protocol Corporate Value Chain Standard.
