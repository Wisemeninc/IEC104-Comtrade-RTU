# Plan: Python RTU with IEC 60870-5-104 for Synthetic TFR

Create a Dockerized Python RTU serving synthetic Transient Fault Records via IEC 60870-5-104. Uses `c104` library, thread-safe queues, SQLite persistence, fixed IOA ranges, and predefined fault type templates. Per IEC 104 standard: clients issue General Interrogation (GI) after connection to receive current data state; new TFRs transmit spontaneously (COT=3) to connected clients.

## Steps

### 1. Create project structure
- `main.py` — application entry point, starts IEC 104 server and FastAPI in parallel threads
- `iec104_server.py` — RTU server using `c104`, handles GI responses and spontaneous transmission
- `tfr_generator.py` — generates synthetic fault data from templates
- `web_api.py` — FastAPI REST endpoints
- `models.py` — Pydantic models and SQLAlchemy ORM
- `database.py` — SQLite persistence layer
- `config.py` — constants, IOA ranges, fault templates
- `Dockerfile`, `requirements.txt`, `docker-compose.yml`

### 2. Define predefined fault templates in `config.py`
Realistic electrical values for each fault type:

- **THREE_PHASE_FAULT**: All phases affected, voltage collapse to ~10%, current surge 5-10× nominal (e.g., 400A → 3000A), duration 80-150ms
- **SINGLE_PHASE_TO_GROUND** (A/B/C variants): One phase voltage drops to ~20%, fault current 3-6× nominal, neutral current present, duration 100-200ms
- **LINE_TO_LINE** (AB/BC/CA variants): Two phases affected, voltage sag to ~50%, current 4-8× nominal, duration 80-120ms
- **DOUBLE_LINE_TO_GROUND**: Two phases + ground, voltage collapse ~15%, high fault current, duration 90-160ms

### 3. Implement IEC 104 server in `iec104_server.py`
Fixed IOA addressing scheme:

| IOA Range | Data Type | Description |
|-----------|-----------|-------------|
| 1000-1009 | `M_EP_TE_1`, `M_EP_TD_1` | Protection start/trip events |
| 1100-1106 | `M_ME_TF_1` | Pre-fault measurements: Va, Vb, Vc, Ia, Ib, Ic, frequency |
| 1200-1206 | `M_ME_TF_1` | Fault measurements: Va, Vb, Vc, Ia, Ib, Ic, frequency |
| 1300-1302 | `M_DP_TB_1`, `M_SP_TB_1` | Status: breaker position, fault active flag |

Protocol behavior:
- Handle General Interrogation (COT=6→7→10) per standard: respond with all current point values
- Transmit new TFR data spontaneously (COT=3) when generated
- Respond to clock synchronization commands (`C_CS_NA_1`, Type 103): accept time from master, confirm with COT=7, use synchronized time for all TFR timestamps

### 4. Build TFR generator in `tfr_generator.py`
- Accept fault type enum from predefined templates
- Generate timestamped sequence:
  1. Pre-fault steady-state
  2. Fault inception
  3. Protection pickup
  4. Trip command
  5. Breaker open
  6. Post-fault
- Add realistic randomization (±5-10% on values, ±10ms on timing)
- Push completed TFR to thread-safe `queue.Queue` for IEC 104 server consumption

### 5. Implement thread-safe coordination
- `tfr_request_queue` (Queue) — web API enqueues `(fault_type, request_id)`
- Background worker thread dequeues, calls generator, updates IEC 104 points
- `tfr_result_dict` (thread-safe dict with Lock) — stores completed TFRs for API retrieval

### 6. Create SQLite persistence in `database.py`
Table schema: `transient_fault_records`
- `id` (INTEGER PRIMARY KEY)
- `created_at` (TIMESTAMP)
- `fault_type` (VARCHAR)
- `duration_ms` (INTEGER)
- `affected_phases` (VARCHAR)
- `pre_fault_json` (JSON)
- `fault_json` (JSON)
- `post_fault_json` (JSON)
- `status` (VARCHAR)

Behavior:
- Load last N records on startup to restore IEC 104 point state
- Save each new TFR immediately after generation

### 7. Implement FastAPI web interface in `web_api.py`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tfr/create` | POST | Body: `{"fault_type": "THREE_PHASE_FAULT"}`, returns TFR id |
| `/api/tfr/types` | GET | Lists available fault types with descriptions |
| `/api/tfr/list` | GET | Paginated list of all TFRs |
| `/api/tfr/{id}` | GET | Full TFR details including all measurements |
| `/api/status` | GET | RTU status (IEC 104 connection count, last TFR timestamp) |
| `/health` | GET | Health check for Docker |

### 8. Containerize with Docker
- **Base image**: `python:3.11-slim`
- **Dependencies**: `c104`, `fastapi`, `uvicorn[standard]`, `sqlalchemy`
- **Exposed ports**: 8080 (HTTP), 2404 (IEC 104)
- **Volume**: `/app/data` for SQLite persistence
- **Health check**: `curl -f http://localhost:8080/health`
- **Environment variables**: `RTU_ADDRESS=1`, `IEC104_PORT=2404`, `WEB_PORT=8080`

## Fault Type Examples

| Fault Type | Phases | Pre-Fault V (kV) | Fault V (kV) | Pre-Fault I (A) | Fault I (A) | Duration |
|------------|--------|------------------|--------------|-----------------|-------------|----------|
| THREE_PHASE_FAULT | A,B,C | 11.0, 11.0, 11.0 | 1.1, 1.1, 1.1 | 400, 400, 400 | 3200, 3200, 3200 | 100ms |
| SINGLE_PHASE_TO_GROUND_A | A | 11.0, 11.0, 11.0 | 2.2, 11.0, 11.0 | 400, 400, 400 | 1800, 400, 400 | 150ms |
| LINE_TO_LINE_AB | A,B | 11.0, 11.0, 11.0 | 5.5, 5.5, 11.0 | 400, 400, 400 | 2400, 2400, 400 | 90ms |
| DOUBLE_LINE_TO_GROUND_AB | A,B | 11.0, 11.0, 11.0 | 1.65, 1.65, 11.0 | 400, 400, 400 | 2800, 2800, 400 | 120ms |
