# COMTRADE Recording Workflow - IEC 104 Signaling

## Overview

This RTU implements the standard IEC 60870-5-104 COMTRADE recording workflow with proper state transitions and spontaneous signaling (COT=3) at each stage.

## IOA Assignments

| IOA  | Type        | Description                    | Initial State |
|------|-------------|--------------------------------|---------------|
| 1500 | M_SP_TB_1   | Recording Active/Busy          | 0 (Idle)      |
| 1501 | M_SP_TB_1   | Recorder Ready                 | 1 (Ready)     |
| 1502 | M_SP_TB_1   | File Ready for Transfer        | 0 (No file)   |
| 1503 | M_ME_NC_1   | Latest TFR ID                  | 0             |

## State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                    NORMAL STATE (Idle)                      │
│  IOA 1500: 0 (Not Recording)                                │
│  IOA 1501: 1 (Ready to Record)                              │
│  IOA 1502: 0 (No File Available)                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ FAULT OCCURS
                   │ (POST /api/tfr/create)
                   ↓
┌─────────────────────────────────────────────────────────────┐
│              RECORDING IN PROGRESS                          │
│  IOA 1500: 1 (Recording Active) ← Spontaneous COT=3         │
│  IOA 1501: 0 (Busy)             ← Spontaneous COT=3         │
│  IOA 1502: 0 (File Not Ready)                               │
│                                                              │
│  RTU captures:                                               │
│  - Pre-fault measurements (50ms before)                      │
│  - Fault measurements (during fault)                         │
│  - Post-fault measurements (100ms after)                     │
│  - Protection events timeline                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ COMTRADE EXPORT REQUESTED
                   │ (GET /api/tfr/{id}/comtrade)
                   ↓
┌─────────────────────────────────────────────────────────────┐
│            RECORDING COMPLETE - FILE READY                  │
│  IOA 1500: 0 (Recording Finished) ← Spontaneous COT=3       │
│  IOA 1501: 1 (Ready for Next)    ← Spontaneous COT=3       │
│  IOA 1502: 1 (File Available)    ← Spontaneous COT=3       │
│  IOA 1503: {TFR_ID}               ← Spontaneous COT=3       │
│                                                              │
│  COMTRADE files generated:                                   │
│  - .cfg (Configuration)                                      │
│  - .dat (Data samples)                                       │
│  - .hdr (Header metadata)                                    │
│  All packaged in ZIP file                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Ready for next fault
                   ↓
            [Returns to NORMAL STATE]
```

## IEC 104 Message Sequence

### 1. Fault Detection (Recording Start)

```
Client                   RTU
  |                      |
  |                      | ← FAULT EVENT
  |                      |
  |<-- M_SP_TB_1 --------|  IOA 1500 = 1 (Recording Active)
  |    COT=3 (Spont)     |  Quality: GOOD, Timestamp
  |                      |
  |<-- M_SP_TB_1 --------|  IOA 1501 = 0 (Recorder Busy)
  |    COT=3 (Spont)     |  Quality: GOOD, Timestamp
  |                      |
  |<-- M_EP_TE_1 --------|  Protection event (IOA 1000-1003)
  |    COT=3 (Spont)     |  Fault inception, pickup, trip
  |                      |
  |<-- M_ME_TF_1 --------|  Fault measurements (IOA 1200-1206)
  |    COT=3 (Spont)     |  Voltage, current, frequency
  |                      |
```

### 2. Recording Complete (File Ready)

```
  |                      |
  |                      | ← COMTRADE Export Triggered
  |                      |
  |<-- M_SP_TB_1 --------|  IOA 1500 = 0 (Recording Finished)
  |    COT=3 (Spont)     |  Quality: GOOD, Timestamp
  |                      |
  |<-- M_SP_TB_1 --------|  IOA 1501 = 1 (Recorder Ready)
  |    COT=3 (Spont)     |  Quality: GOOD, Timestamp
  |                      |
  |<-- M_SP_TB_1 --------|  IOA 1502 = 1 (File Ready)
  |    COT=3 (Spont)     |  Quality: GOOD, Timestamp
  |                      |
  |<-- M_ME_NC_1 --------|  IOA 1503 = {TFR_ID}
  |    COT=3 (Spont)     |  Which fault record is available
  |                      |
```

## Testing the Workflow

### Using cURL

```bash
# 1. Check initial state (should be idle, ready)
curl http://localhost:8080/api/status | jq '.comtrade_recording_active, .comtrade_recorder_ready, .comtrade_file_ready'
# Expected: false, true, false

# 2. Generate a fault (triggers recording start)
curl -X POST http://localhost:8080/api/tfr/create \
  -H "Content-Type: application/json" \
  -d '{"fault_type":"THREE_PHASE_FAULT"}' | jq '.id'
# Save the TFR ID

# 3. Check status (should show recording active)
curl http://localhost:8080/api/status | jq '.comtrade_recording_active, .comtrade_recorder_ready'
# Expected: true, false

# 4. Export COMTRADE (triggers recording complete)
TFR_ID=16  # Use ID from step 2
curl http://localhost:8080/api/tfr/$TFR_ID/comtrade -o comtrade.zip

# 5. Check final status (should show file ready)
curl http://localhost:8080/api/status | jq '.comtrade_recording_active, .comtrade_recorder_ready, .comtrade_file_ready, .comtrade_latest_tfr_id'
# Expected: false, true, true, 16
```

### Using Web Dashboard

1. **Open Dashboard**: http://localhost:8080
2. **Initial State**: COMTRADE signals section shows:
   - Recording Active (1500): ⚪ Idle
   - Recorder Ready (1501): ✅ Ready
   - File Ready (1502): ⏳ None

3. **Generate Fault**: Click any fault button (e.g., "3-Phase Fault")
   - IOA 1500 changes to: 🔴 Recording
   - IOA 1501 changes to: ⏸️ Busy
   - IOA 1502 remains: ⏳ None

4. **Export COMTRADE**: Click a TFR in "Recent Fault Records"
   - IOA 1500 changes to: ⚪ Idle
   - IOA 1501 changes to: ✅ Ready
   - IOA 1502 changes to: 📦 Available
   - IOA 1503 shows TFR ID

### Using IEC 104 Client

```python
import c104
import time

# Connect to RTU
client = c104.Client()
connection = client.add_connection(ip="localhost", port=2404, init=c104.Init.INTERROGATION)
station = connection.add_station(common_address=1)

# Subscribe to COMTRADE signals
def on_point_change(point: c104.Point, previous_state: c104.Quality, previous_value):
    ioa = point.io_address
    value = point.value
    timestamp = point.timestamp
    
    if ioa == 1500:
        print(f"Recording Active: {value} at {timestamp}")
    elif ioa == 1501:
        print(f"Recorder Ready: {value} at {timestamp}")
    elif ioa == 1502:
        print(f"File Ready: {value} at {timestamp}")
    elif ioa == 1503:
        print(f"Latest TFR ID: {int(value)} at {timestamp}")

# Add monitoring points
station.add_point(1500, c104.Type.M_SP_TB_1, report_ms=0).on_receive(on_point_change)
station.add_point(1501, c104.Type.M_SP_TB_1, report_ms=0).on_receive(on_point_change)
station.add_point(1502, c104.Type.M_SP_TB_1, report_ms=0).on_receive(on_point_change)
station.add_point(1503, c104.Type.M_ME_NC_1, report_ms=0).on_receive(on_point_change)

# Connect and start monitoring
connection.start()
time.sleep(60)  # Monitor for 1 minute
connection.stop()
```

## Implementation Details

### Backend Code Flow

**1. Fault Generation** ([web_api.py](web_api.py:75-90))
```python
# When POST /api/tfr/create is called:
tfr_id = db.save_tfr(tfr_data)
background_tasks.add_task(iec104_server.signal_comtrade_recording_start, tfr_id)
background_tasks.add_task(iec104_server.update_tfr_data, tfr_detail)
```

**2. Recording Start Signal** ([iec104_server.py](iec104_server.py:228-263))
```python
def signal_comtrade_recording_start(self, tfr_id: int):
    # Update state: Recording now active, recorder busy
    self.current_data[IOARange.COMTRADE_RECORDING_ACTIVE] = True
    self.current_data[IOARange.COMTRADE_RECORDER_READY] = False
    
    # Send spontaneous signals (COT=3)
    point = self.station.get_point(IOARange.COMTRADE_RECORDING_ACTIVE)
    point.value = True
    point.transmit(cause=c104.Cot.SPONTANEOUS)
    
    point = self.station.get_point(IOARange.COMTRADE_RECORDER_READY)
    point.value = False
    point.transmit(cause=c104.Cot.SPONTANEOUS)
```

**3. COMTRADE Export** ([web_api.py](web_api.py:175-181))
```python
# When GET /api/tfr/{id}/comtrade is called:
files = export_tfr_to_comtrade(tfr, output_dir, sample_rate)
create_zip(files)
iec104_server.signal_comtrade_recording_complete(tfr_id)
```

**4. Recording Complete Signal** ([iec104_server.py](iec104_server.py:265-314))
```python
def signal_comtrade_recording_complete(self, tfr_id: int):
    # Update state: Recording finished, file ready
    self.current_data[IOARange.COMTRADE_RECORDING_ACTIVE] = False
    self.current_data[IOARange.COMTRADE_RECORDER_READY] = True
    self.current_data[IOARange.COMTRADE_FILE_READY] = True
    self.current_data[IOARange.COMTRADE_LATEST_TFR_ID] = float(tfr_id)
    
    # Send all state transitions spontaneously (COT=3)
    # IOA 1500 = 0, 1501 = 1, 1502 = 1, 1503 = TFR_ID
```

## Advantages of This Approach

1. **Standards Compliant**: Follows IEC 60870-5-104 COMTRADE signaling conventions
2. **Real-time Awareness**: Clients know immediately when:
   - Recording starts (fault detected)
   - Recording completes (file being generated)
   - File is ready for transfer
3. **State Tracking**: Three distinct states prevent ambiguity
4. **Spontaneous Transmission**: Uses COT=3 for event-driven updates
5. **File Management**: TFR ID (IOA 1503) identifies which fault's COMTRADE is available
6. **Multi-file Support**: Available count tracks multiple COMTRADE files

## Comparison with Previous Implementation

| Aspect | Old (File Export Only) | New (Recording Workflow) |
|--------|------------------------|--------------------------|
| Signal timing | Only on export | Start on fault, complete on export |
| State granularity | Binary (available/not) | Three states (idle/recording/ready) |
| Fault awareness | No | Yes (IOA 1500 changes on fault) |
| Recording status | Unknown | Tracked (IOA 1501) |
| Client experience | Poll for files | Real-time status updates |
| IEC 104 compliance | Partial | Full standard workflow |

## References

- [IEC 60870-5-104 Standard](https://webstore.iec.ch/publication/3748)
- [IEEE C37.111-2013 COMTRADE Format](https://standards.ieee.org/standard/C37_111-2013.html)
- [IEC104_COMTRADE_SIGNALS.md](IEC104_COMTRADE_SIGNALS.md) - Original implementation notes
- [README.md](README.md) - System overview and setup
