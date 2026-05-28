# TRADEOFFS.md — Intentionally Skipped Features

## 1. Real-Time Celery Task Queue (Replaced with Threading)

**What was skipped**: Full async ingestion via Celery + Redis with task progress tracking, retry logic, and dead-letter queuing.

**What was built instead**: Python `threading.Thread` daemon for background ingestion.

**Why skipped**: 
- Celery requires Redis to be running, adding a hard deployment dependency
- For a solo developer demo environment, threading is functionally equivalent
- The Celery scaffolding (`core/celery.py`) is in place — switching requires only changing the `run_ingestion()` call in `ingestion/views.py` to a Celery `.delay()` call

**Production consequence**: Under concurrent upload load, threading will not scale horizontally. Memory leaks are possible if threads don't complete. **Celery is required for production.**

---

## 2. Row-Level PostgreSQL Security (Replaced with ORM Filtering)

**What was skipped**: PostgreSQL Row-Level Security (RLS) policies enforcing tenant isolation at the database layer.

**What was built instead**: Every queryset filters by `tenant=request.tenant` at the ORM level.

**Why skipped**:
- RLS requires database superuser permissions to configure
- Django's ORM tenant filtering is correct for 99% of use cases and is far simpler to test
- RLS becomes essential when tenant isolation must be enforced even if application code has bugs — a higher-security requirement than this assignment demands

**Production consequence**: A single ORM filtering bug could theoretically leak cross-tenant data. Mitigated by consistent `.filter(tenant=request.tenant)` pattern and Django's queryset isolation.

---

## 3. Configurable Emission Factor Tables per Tenant

**What was skipped**: Tenant-specific emission factor databases (e.g., letting ACME Corp use their custom grid emission factor from their utility provider's sustainability report).

**What was built instead**: Static GHG Protocol 2023 / IEA 2023 emission factors in `utils/emission_factors.py`.

**Why skipped**:
- Emission factor management is a full product feature: version control, regulatory jurisdiction mapping, audit trail, effectivity dates
- Building it properly would double the backend scope
- The static factor library covers 95% of demo/test needs

**Production consequence**: Enterprise customers will require configurable EFs, especially for Scope 2 market-based accounting (supplier-specific residual mix). This is the highest-priority missing feature for a real product launch.
