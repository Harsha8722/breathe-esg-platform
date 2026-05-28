# SOURCES.md — Data Realism Research

## Researched Enterprise Formats

### SAP ECC / S4HANA
- **Source**: SAP Help Portal (help.sap.com), SAP Community Network
- **Key fields**: BUDAT (Buchungsdatum/Posting Date), MATNR (Material Number), MENGE (Quantity), MEINS (Unit), WERKS (Plant), KOSTL (Cost Center), LIFNR (Vendor)
- **Real-world quirk**: SAP exports from European subsidiaries often use German/French field labels; US subsidiaries use English. Tested with both in column alias dictionary.
- **Fuel types**: SAP material descriptions are free-text. "Diesel Kraftstoff" (German), "Gasoil", "GO", "HVO", "B7" all refer to diesel variants. The normalizer handles ~12 variants.

### Utility Electricity (Smart Meters / Billing)
- **Source**: UK MPAN format (Elexon), US ESPI standard (Green Button initiative), DEWA (Dubai), AEMO (Australia)
- **Key quirk**: UK uses MPAN (13-digit meter reference); Australia uses NMI (10-char); US uses ESI-ID. All mapped to `meter_id`.
- **Billing cycle**: Most utilities bill monthly but some commercial accounts bill quarterly. Overlapping cycles occur when utilities issue amended bills for previous periods — modeled as a suspicious flag.

### Corporate Travel (Concur / Navan)
- **Source**: SAP Concur export templates, Navan API documentation, GBTA expense report standards
- **Key fields**: Expense types match Concur's out-of-box categories: "Air", "Hotel", "Rail", "Ground Transportation"
- **Distance data**: Concur does NOT include flight distances in most export formats — distances must be calculated from airport pairs. This is a known limitation in all T&E platforms.

---

## Sample Data Realism

| File | Realistic Elements | Intentional Defects |
|------|-------------------|---------------------|
| `sap_fuel_export_q1_2024.csv` | Multilingual headers, plant codes, real vendor names, mixed units | Zero qty, missing qty, INVALID qty, exact duplicate row, suspicious 95,000L spike |
| `utility_electricity_q1_2024.csv` | Real meter ID formats (MTR-UK-0001), regional tariff names, MWh vs kWh | Overlapping billing period, missing usage, negative usage, invalid date, 5.4M kWh spike |
| `corporate_travel_q1_2024.csv` | Real airport codes (JFK/LHR/BOM), travel classes, realistic prices | Missing distance, invalid amount, unknown expense type, missing origin/destination |

---

## Emission Factor Sources

| Category | Source | Version |
|----------|--------|---------|
| Fuel combustion | IPCC 2006, GHG Protocol 2023 | GHG Protocol Corporate Standard |
| Purchased electricity | IEA World Energy Outlook 2023 | Grid emission factors by country |
| Business travel - flights | DEFRA/BEIS 2023 | UK Government GHG Conversion Factors |
| Hotels | HCMI (Hotel Carbon Measurement Initiative) | 2022 average |

---

## Limitations

1. **Emission factors are static**: No temporal adjustment for grid decarbonization over time
2. **Currency conversion is not implemented**: Cost data is stored but not normalized
3. **No supplier-specific Scope 3 factors**: Category 1 (Purchased Goods) not supported
4. **Airport distance table covers ~16 routes**: Only major international pairs. Domestic routes use a `distance unknown` flag.
5. **No fugitive emissions**: Refrigerant leaks, methane venting not modeled

---

## What Would Fail at Production Scale

1. **Single-process ingestion**: 500k-row SAP exports would time out in a single HTTP request without Celery
2. **No pandas chunking**: Large files read fully into memory — 50MB CSV with wide columns could use >500MB RAM
3. **Static emission factors**: A multinational with 50+ subsidiaries needs jurisdiction-specific factors with version control
4. **Thread-based async**: Not compatible with Gunicorn multi-worker mode — race conditions possible
5. **No file virus scanning**: Uploaded files should pass through ClamAV or equivalent before parsing
6. **No rate limiting**: Upload endpoint has no request throttling — DDoS vector
