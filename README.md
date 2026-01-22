# Python RTU with IEC 60870-5-104 for Synthetic TFR

A Dockerized Python RTU (Remote Terminal Unit) that serves synthetic Transient Fault Records (TFR) via the IEC 60870-5-104 protocol. This implementation uses the `c104` library, thread-safe queues, SQLite persistence, and predefined fault type templates to simulate realistic electrical fault scenarios.

## Features

- **IEC 60870-5-104 Protocol**: Full implementation with General Interrogation (GI) support and spontaneous transmission (COT=3)
- **Synthetic TFR Generation**: 10 predefined fault types with realistic electrical characteristics
- **COMTRADE Export**: IEEE C37.111-2013 standard format for fault data exchange (.cfg, .dat, .hdr files)
- **COMTRADE Recording Workflow**: Standard IEC 104 signaling for recording status (idle → recording → file ready)
- **REST API**: FastAPI-based web interface for TFR management
- **SQLite Persistence**: Store and retrieve historical fault records
- **Docker Support**: Complete containerization with health checks
- **Thread-Safe**: Parallel operation of IEC 104 and HTTP servers
- **Clock Synchronization**: Accepts C_CS_NA_1 commands from master stations

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

The service will be available at:
- **REST API**: http://localhost:8080
- **IEC 104**: localhost:2404
- **Web Dashboard**: http://localhost:8080

## Web Dashboard

Access the interactive web dashboard at **http://localhost:8080**

The dashboard provides:
- **Real-time IEC 104 monitoring** - View all data points (IOA 1100-1502)
- **Fault generation** - One-click buttons for all 10 fault types
- **Live measurements** - Pre-fault and fault voltage, current, frequency
- **Status indicators** - IEC 104 connections, breaker position, COMTRADE availability
- **Recent TFRs** - List of generated fault records with COMTRADE export
- **Auto-refresh** - Updates every 5 seconds

![Dashboard Features](static/dashboard-preview.png)

### Dashboard Sections

1. **Status Bar** - IEC 104 port, connected clients, total TFRs, COMTRADE count
2. **Fault Generator** - Buttons for generating all fault types
3. **Pre-Fault Measurements** (IOA 1100-1106) - Normal operating conditions
4. **Fault Measurements** (IOA 1200-1206) - Fault condition values
5. **Status Points** (IOA 1300-1302) - Breaker, fault flags
6. **COMTRADE Recording Signals** (IOA 1500-1503) - Recording workflow status
7. **Recent Fault Records** - Click to view details and export COMTRADE

**COMTRADE Recording Workflow:**
- Generate fault → IOA 1500 = 🔴 Recording, IOA 1501 = ⏸️ Busy
- Export COMTRADE → IOA 1500 = ⚪ Idle, IOA 1501 = ✅ Ready, IOA 1502 = 📦 Available
- See [COMTRADE_RECORDING_WORKFLOW.md](COMTRADE_RECORDING_WORKFLOW.md) for details

### Using Docker

```bash
# Build image
docker build -t rtu-iec104 .

# Run container
docker run -d \
  -p 8080:8080 \
  -p 2404:2404 \
  -v $(pwd)/data:/app/data \
  --name rtu \
  rtu-iec104
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## API Documentation

### Health Check

```bash
GET /health
```

Returns service health status.

### Get RTU Status

```bash
GET /api/status
```

Returns operational status including connected IEC 104 clients and last TFR timestamp.

**Response:**
```json
{
  "iec104_port": 2404,
  "iec104_connected_clients": 2,
  "web_port": 8080,
  "last_tfr_timestamp": "2026-01-09T12:34:56.789Z",
  "total_tfrs_generated": 42,
  "database_path": "sqlite:///./data/rtu.db",
  "comtrade_available_count": 5,
  "latest_comtrade_tfr_id": 42
}
```

### List Available Fault Types

```bash
GET /api/tfr/types
```

Returns all available fault types with descriptions.

**Response:**
```json
[
  {
    "name": "THREE_PHASE_FAULT",
    "description": "Balanced three-phase fault - all phases affected equally",
    "affected_phases": ["A", "B", "C"],
    "typical_duration_ms": "80-150"
  },
  ...
]
```

### Create New TFR

```bash
POST /api/tfr/create
Content-Type: application/json

{
  "fault_type": "THREE_PHASE_FAULT"
}
```

Generates a new TFR and transmits it spontaneously via IEC 104 to all connected clients.

**Response:**
```json
{
  "id": 1,
  "fault_type": "THREE_PHASE_FAULT",
  "status": "completed",
  "created_at": "2026-01-09T12:34:56.789Z"
}
```

### List TFRs

```bash
GET /api/tfr/list?page=1&page_size=20
```

Returns paginated list of all TFRs.

**Response:**
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "records": [...]
}
```

### Get TFR Details

```bash
GET /api/tfr/{id}
```

Returns complete TFR with all measurements and events.

**Response:**
```json
{
  "id": 1,
  "created_at": "2026-01-09T12:34:56.789Z",
  "fault_type": "THREE_PHASE_FAULT",
  "duration_ms": 112,
  "affected_phases": ["A", "B", "C"],
  "status": "completed",
  "pre_fault": {
    "timestamp": "2026-01-09T12:34:56.739Z",
    "voltage_kv": {"A": 11.2, "B": 10.9, "C": 11.1},
    "current_a": {"A": 395.5, "B": 408.2, "C": 402.1},
    "frequency_hz": 50.02
  },
  "fault": {
    "timestamp": "2026-01-09T12:34:56.799Z",
    "voltage_kv": {"A": 1.15, "B": 1.08, "C": 1.12},
    "current_a": {"A": 3280.5, "B": 3150.2, "C": 3201.8},
    "frequency_hz": 49.78
  },
  "post_fault": {...},
  "events": [...]
}
```

### Export TFR in COMTRADE Format

```bash
GET /api/tfr/{id}/comtrade?sample_rate=4000
```

Downloads TFR in **COMTRADE (IEEE C37.111)** format as a ZIP file containing:
- **.cfg** - Configuration file with channel definitions
- **.dat** - ASCII data file with time-stamped waveforms
- **.hdr** - Header file with fault metadata

**Automatically signals COMTRADE recording completion via IEC 104 spontaneous transmission (IOA 1500-1503).**

**Parameters:**
- `sample_rate` (optional): Sampling rate in Hz (1000-16000, default: 4000 Hz = 80 samples/cycle @ 50Hz)

**Example:**
```bash
# Download single TFR in COMTRADE format
curl -o tfr_001.zip "http://localhost:8080/api/tfr/1/comtrade?sample_rate=4000"

# Extract files
unzip tfr_001.zip
# Contains: TFR_0001_THREE_PHASE_FAULT_20260109_123456.cfg
#           TFR_0001_THREE_PHASE_FAULT_20260109_123456.dat
#           TFR_0001_THREE_PHASE_FAULT_20260109_123456.hdr
```

**IEC 104 Spontaneous Recording Workflow (COT=3):**

When fault occurs (POST /api/tfr/create):
- **IOA 1500**: `True` (Recording Active)
- **IOA 1501**: `False` (Recorder Busy)

When COMTRADE exported (GET /api/tfr/{id}/comtrade):
- **IOA 1500**: `False` (Recording Complete)
- **IOA 1501**: `True` (Recorder Ready)
- **IOA 1502**: `True` (File Ready for Transfer)
- **IOA 1503**: `{TFR_ID}` (Which fault record is available)

See **[COMTRADE Recording Workflow Guide](COMTRADE_RECORDING_WORKFLOW.md)** for complete state machine and testing procedures.
```

### Batch Export All TFRs in COMTRADE Format

```bash
GET /api/tfr/export/comtrade/batch?sample_rate=4000&limit=100
```

Downloads all TFRs as a single ZIP archive, with each TFR in its own folder.

**Parameters:**
- `sample_rate` (optional): Sampling rate in Hz (default: 4000)
- `limit` (optional): Maximum TFRs to export (1-1000, default: 100)

**Example:**
```bash
# Export all TFRs
curl -o all_tfrs.zip "http://localhost:8080/api/tfr/export/comtrade/batch"
```

## COMTRADE Format Details

For comprehensive information about COMTRADE export, including:
- File format specifications (IEEE C37.111-2013)
- Channel definitions and sampling rates
- Integration with analysis software
- Batch processing and automation
- Troubleshooting guide

See the detailed **[COMTRADE Export Guide](COMTRADE_EXPORT_GUIDE.md)**.

COMTRADE files are compatible with standard power system analysis tools including SEL AcSELerator, PSCAD, EMTP, DIgSILENT PowerFactory, and other industry-standard fault analysis software.

## IEC 104 COMTRADE Availability Signaling

The RTU signals COMTRADE file availability through **IEC 60870-5-104 spontaneous data transmission**. When a COMTRADE export is generated, three data points are automatically sent:

- **IOA 1500** (`M_SP_TB_1`) - COMTRADE Available Flag (True/False)
- **IOA 1501** (`M_ME_NC_1`) - TFR ID for which COMTRADE is ready
- **IOA 1502** (`M_ME_NC_1`) - Total number of COMTRADE files available

This enables SCADA systems and IEC 104 clients to be immediately notified when COMTRADE files are ready for download, without polling or requiring separate webhook infrastructure.

**Benefits:**
- ✓ Native to IEC 104 protocol (no additional infrastructure)
- ✓ Real-time spontaneous notification (COT=3)
- ✓ Queryable via General Interrogation
- ✓ Works with existing SCADA connections and firewall rules

For complete details and client integration examples, see **[IEC 104 COMTRADE Signals Guide](IEC104_COMTRADE_SIGNALS.md)**.

## IEC 60870-5-104 Implementation

### IOA Address Mapping

| IOA Range | Data Type | Description |
|-----------|-----------|-------------|
| 1000-1009 | `M_EP_TE_1`, `M_EP_TD_1` | Protection start/trip events |
| 1100-1106 | `M_ME_TF_1` | Pre-fault measurements: Va, Vb, Vc, Ia, Ib, Ic, frequency |
| 1200-1206 | `M_ME_TF_1` | Fault measurements: Va, Vb, Vc, Ia, Ib, Ic, frequency |
| 1300-1302 | `M_DP_TB_1`, `M_SP_TB_1` | Status: breaker position, fault active flag |
| 1400 | `M_ME_TD_1` | Device clock (normalized value) |
| **1500-1502** | `M_SP_TB_1`, `M_ME_NC_1` | **COMTRADE availability signals: flag, TFR ID, file count** |

### Protocol Behavior

1. **Connection**: IEC 104 clients connect to port 2404
2. **General Interrogation**: Client sends GI command (COT=6), RTU responds with all current point values (COT=7→10)
3. **Spontaneous Transmission**: When new TFR is generated, RTU transmits data points with COT=3
4. **Clock Synchronization**: RTU accepts C_CS_NA_1 commands and confirms with COT=7

### Example Client Connection (Python with c104)

```python
import c104

# Create client
client = c104.Client()
connection = client.add_connection(ip="localhost", port=2404)
station = connection.add_station(common_address=1)

# Add data points to receive
station.add_point(io_address=1100, type=c104.Type.M_ME_TF_1)  # Pre-fault Va
station.add_point(io_address=1200, type=c104.Type.M_ME_TF_1)  # Fault Va

# Connect and start
connection.start()

# Send General Interrogation
station.interrogation()
```

## Fault Types

### Available Fault Types

1. **THREE_PHASE_FAULT**: Balanced three-phase fault, all phases collapse to ~10% voltage
2. **SINGLE_PHASE_TO_GROUND_A/B/C**: Single phase to ground, affected phase drops to ~20%
3. **LINE_TO_LINE_AB/BC/CA**: Phase-to-phase fault, affected phases sag to ~50%
4. **DOUBLE_LINE_TO_GROUND_AB/BC/CA**: Two phases to ground, ~15% remaining voltage

### Realistic Characteristics

Each fault type includes:
- Pre-fault steady-state values (11 kV, 400 A, 50 Hz)
- Fault conditions with voltage collapse and current surge
- Protection event sequence (pickup → trip → breaker operation)
- Randomized timing and values (±5-10% variation)
- Typical durations: 80-200ms

## Project Structure

```
/github/RTU/
├── main.py                     # Application entry point
├── iec104_server.py            # IEC 104 server implementation
├── web_api.py                  # FastAPI REST endpoints
├── tfr_generator.py            # Fault data generator
├── comtrade_export.py          # COMTRADE format exporter
├── models.py                   # Pydantic and SQLAlchemy models
├── database.py                 # SQLite persistence layer
├── config.py                   # Configuration and templates
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Docker Compose configuration
├── README.md                   # This file
├── IEC104_COMTRADE_SIGNALS.md  # IEC 104 COMTRADE signaling guide
├── COMTRADE_EXPORT_GUIDE.md    # Detailed COMTRADE export documentation
└── COMTRADE_WEB_API_RATIONALE.md  # Design rationale and standards
```

## Configuration

Environment variables (can be set in docker-compose.yml):

- `RTU_ADDRESS`: Common address for IEC 104 station (default: 1)
- `IEC104_PORT`: IEC 104 server port (default: 2404)
- `WEB_PORT`: HTTP API port (default: 8080)

## Data Persistence

TFR records are stored in SQLite database at `./data/rtu.db`. The database persists:
- Fault type and affected phases
- Pre-fault, fault, and post-fault measurements
- Event timestamps and descriptions
- Fault duration and status

On startup, the RTU loads the most recent TFR to restore IEC 104 data points.

## Testing

### Test API Endpoints

```bash
# Check health
curl http://localhost:8080/health

# Get status
curl http://localhost:8080/api/status

# List fault types
curl http://localhost:8080/api/tfr/types

# Create three-phase fault
curl -X POST http://localhost:8080/api/tfr/create \
  -H "Content-Type: application/json" \
  -d '{"fault_type": "THREE_PHASE_FAULT"}'

# Get TFR details
curl http://localhost:8080/api/tfr/1

# Export TFR in COMTRADE format
curl -o tfr_001.zip "http://localhost:8080/api/tfr/1/comtrade"

# Export all TFRs in COMTRADE format
curl -o all_tfrs.zip "http://localhost:8080/api/tfr/export/comtrade/batch"
```

### COMTRADE File Contents

The COMTRADE export includes:

**Analog Channels (7):**
1. Va - Phase A Voltage (kV)
2. Vb - Phase B Voltage (kV)
3. Vc - Phase C Voltage (kV)
4. Ia - Phase A Current (A)
5. Ib - Phase B Current (A)
6. Ic - Phase C Current (A)
7. Freq - System Frequency (Hz)

**Digital Channels (5):**
1. BKR_52 - Circuit Breaker Status (1=closed, 0=open)
2. FAULT_ACT - Fault Active Flag (1=active, 0=cleared)
3. PROT_ARM - Protection Armed (1=armed)
4. TRIP_CMD - Trip Command Issued (1=active)
5. PICKUP - Protection Pickup (1=active)

**Sampling:** Default 4000 Hz (80 samples/cycle @ 50Hz), configurable from 1000-16000 Hz

**Compatible with:** PSCAD, EMTP, DIgSILENT PowerFactory, SEL AcSELerator, and other standard fault analysis tools.

### Test IEC 104 Connection

Use any IEC 104 client software or the `c104` Python library to connect to port 2404 and perform General Interrogation.

## Development

### Adding New Fault Types

1. Add fault template to `FAULT_TEMPLATES` in [config.py](config.py)
2. Define affected phases, voltage/current characteristics, and timing
3. Fault type will automatically appear in API and be available for generation

### Extending IOA Ranges

1. Add new IOA constants to `IOARange` class in [config.py](config.py)
2. Add data point creation in `iec104_server.py` `_add_data_points()`
3. Update `_transmit_spontaneous()` to include new points

## License

MIT License - See LICENSE file for details

## References

- IEC 60870-5-104 Protocol Standard
- [c104 Library Documentation](https://github.com/Fraunhofer-FIT-DIEN/lib60870)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
