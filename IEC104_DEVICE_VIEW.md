# IEC 60870-5-104 Device View - RTU Synthetic TFR

## Device Overview from SCADA/Control System Perspective

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     RTU SYNTHETIC TFR GENERATOR                              │
│                     IEC 60870-5-104 Remote Terminal Unit                     │
└─────────────────────────────────────────────────────────────────────────────┘

Connection Details:
  Protocol:        IEC 60870-5-104 (TCP/IP)
  IP Address:      0.0.0.0 (listening on all interfaces)
  Port:            2404 (standard IEC 104 port)
  Common Address:  1
  Device Type:     RTU (Remote Terminal Unit)
  Function:        Transient Fault Record Generator
```

## Information Object Address (IOA) Map

### Pre-Fault Measurements (IOA 1100-1106)
**Type:** M_ME_TF_1 (Measured value, short floating point with time tag)

```
┌────────┬─────────────────────────────────┬──────┬─────────────┬──────────────┐
│  IOA   │ Description                     │ Unit │ Type        │ Update Rate  │
├────────┼─────────────────────────────────┼──────┼─────────────┼──────────────┤
│  1100  │ Phase A Voltage (Pre-Fault)     │ kV   │ M_ME_TF_1   │ Spontaneous  │
│  1101  │ Phase B Voltage (Pre-Fault)     │ kV   │ M_ME_TF_1   │ Spontaneous  │
│  1102  │ Phase C Voltage (Pre-Fault)     │ kV   │ M_ME_TF_1   │ Spontaneous  │
│  1103  │ Phase A Current (Pre-Fault)     │ A    │ M_ME_TF_1   │ Spontaneous  │
│  1104  │ Phase B Current (Pre-Fault)     │ A    │ M_ME_TF_1   │ Spontaneous  │
│  1105  │ Phase C Current (Pre-Fault)     │ A    │ M_ME_TF_1   │ Spontaneous  │
│  1106  │ Frequency (Pre-Fault)           │ Hz   │ M_ME_TF_1   │ Spontaneous  │
└────────┴─────────────────────────────────┴──────┴─────────────┴──────────────┘

Normal Operating Values:
  Voltages:  ~11.0 kV  (±5% variation)
  Currents:  ~400 A    (±10% variation)
  Frequency: ~50.0 Hz  (±0.05 Hz variation)
```

### Fault Measurements (IOA 1200-1206)
**Type:** M_ME_TF_1 (Measured value, short floating point with time tag)

```
┌────────┬─────────────────────────────────┬──────┬─────────────┬──────────────┐
│  IOA   │ Description                     │ Unit │ Type        │ Update Rate  │
├────────┼─────────────────────────────────┼──────┼─────────────┼──────────────┤
│  1200  │ Phase A Voltage (Fault)         │ kV   │ M_ME_TF_1   │ Spontaneous  │
│  1201  │ Phase B Voltage (Fault)         │ kV   │ M_ME_TF_1   │ Spontaneous  │
│  1202  │ Phase C Voltage (Fault)         │ kV   │ M_ME_TF_1   │ Spontaneous  │
│  1203  │ Phase A Current (Fault)         │ A    │ M_ME_TF_1   │ Spontaneous  │
│  1204  │ Phase B Current (Fault)         │ A    │ M_ME_TF_1   │ Spontaneous  │
│  1205  │ Phase C Current (Fault)         │ A    │ M_ME_TF_1   │ Spontaneous  │
│  1206  │ Frequency (Fault)               │ Hz   │ M_ME_TF_1   │ Spontaneous  │
└────────┴─────────────────────────────────┴──────┴─────────────┴──────────────┘

Fault Condition Values (Example - Three-Phase Fault):
  Voltages:  ~1.0-2.0 kV  (10-20% of normal - severe voltage sag)
  Currents:  ~2400-3500 A (6-9× nominal - fault current surge)
  Frequency: ~49.75-49.85 Hz (slight frequency drop during fault)
```

### Status/Digital Points (IOA 1300-1302)

```
┌────────┬─────────────────────────────────┬─────────────┬──────────────────────┐
│  IOA   │ Description                     │ Type        │ States               │
├────────┼─────────────────────────────────┼─────────────┼──────────────────────┤
│  1300  │ Circuit Breaker Position        │ M_DP_TB_1   │ 0=Intermediate       │
│        │                                 │             │ 1=OFF/OPEN           │
│        │                                 │             │ 2=ON/CLOSED          │
├────────┼─────────────────────────────────┼─────────────┼──────────────────────┤
│  1301  │ Fault Active Flag               │ M_SP_TB_1   │ 0=Inactive/Cleared   │
│        │                                 │             │ 1=Active/Faulted     │
├────────┼─────────────────────────────────┼─────────────┼──────────────────────┤
│  1302  │ Protection Armed                │ M_SP_TB_1   │ 0=Disarmed           │
│        │                                 │             │ 1=Armed/Ready        │
└────────┴─────────────────────────────────┴─────────────┴──────────────────────┘
```

### COMTRADE Recording Signals (IOA 1500-1503)
**Type:** M_SP_TB_1 (Single point with time), M_ME_NC_1 (Short floating point)

```
┌────────┬─────────────────────────────────┬─────────────┬──────────────────────┐
│  IOA   │ Description                     │ Type        │ States               │
├────────┼─────────────────────────────────┼─────────────┼──────────────────────┤
│  1500  │ Recording Active/Busy           │ M_SP_TB_1   │ 0=Idle               │
│        │                                 │             │ 1=Recording          │
├────────┼─────────────────────────────────┼─────────────┼──────────────────────┤
│  1501  │ Recorder Ready                  │ M_SP_TB_1   │ 0=Busy/Not Ready     │
│        │                                 │             │ 1=Ready to Record    │
├────────┼─────────────────────────────────┼─────────────┼──────────────────────┤
│  1502  │ File Ready for Transfer         │ M_SP_TB_1   │ 0=No File            │
│        │                                 │             │ 1=File Available     │
├────────┼─────────────────────────────────┼─────────────┼──────────────────────┤
│  1503  │ Latest TFR ID                   │ M_ME_NC_1   │ Float: TFR ID        │
└────────┴─────────────────────────────────┴─────────────┴──────────────────────┘

COMTRADE Recording Workflow:
  Normal State:    1500=0 (Idle), 1501=1 (Ready), 1502=0 (No File)
  ↓ Fault Occurs
  Recording:       1500=1 (Active), 1501=0 (Busy), 1502=0 (Processing)
  ↓ Export Triggered
  File Ready:      1500=0 (Done), 1501=1 (Ready), 1502=1 (Available), 1503={TFR_ID}

See: COMTRADE_RECORDING_WORKFLOW.md for detailed state machine
```

### Protection Events (IOA 1000-1009)
**Type:** M_EP_TE_1, M_EP_TD_1 (Event of protection equipment with time tag)

```
┌────────┬─────────────────────────────────┬─────────────┬──────────────────────┐
│  IOA   │ Description                     │ Type        │ Event                │
├────────┼─────────────────────────────────┼─────────────┼──────────────────────┤
│  1000  │ Protection Start/Pickup         │ M_EP_TE_1   │ Fault detection      │
│  1001  │ Protection Trip Command         │ M_EP_TE_1   │ Trip issued          │
│  1002  │ Fault Detected                  │ M_EP_TE_1   │ Fault inception      │
│  1003  │ Circuit Breaker Open Event      │ M_EP_TD_1   │ Breaker operated     │
└────────┴─────────────────────────────────┴─────────────┴──────────────────────┘
```

## Protocol Behavior

### 1. Connection Establishment

```
Client                                    RTU
  │                                        │
  │──────── TCP Connect (port 2404) ────→│
  │                                        │
  │←─────── TCP ACK + STARTDT ───────────│
  │                                        │
  │──────── STARTDT ACK ─────────────────→│
  │                                        │
  └────── Connection Established ─────────┘
```

### 2. General Interrogation (GI)

When a client connects, it should issue a General Interrogation to get the current state:

```
Client                                    RTU
  │                                        │
  │──── C_IC_NA_1 (GI, COT=6) ──────────→│  Interrogation Command
  │                                        │
  │←─── C_IC_NA_1 (GI, COT=7) ───────────│  ACK (Activation Confirmation)
  │                                        │
  │←─── M_ME_TF_1 (IOA 1100, COT=20) ────│  Va Pre-Fault = 11.0 kV
  │←─── M_ME_TF_1 (IOA 1101, COT=20) ────│  Vb Pre-Fault = 11.0 kV
  │←─── M_ME_TF_1 (IOA 1102, COT=20) ────│  Vc Pre-Fault = 11.0 kV
  │←─── M_ME_TF_1 (IOA 1103, COT=20) ────│  Ia Pre-Fault = 400 A
  │      ... (all data points) ...        │
  │←─── M_DP_TB_1 (IOA 1300, COT=20) ────│  Breaker = CLOSED (2)
  │←─── M_SP_TB_1 (IOA 1301, COT=20) ────│  Fault Active = FALSE (0)
  │←─── M_SP_TB_1 (IOA 1302, COT=20) ────│  Protection = ARMED (1)
  │                                        │
  │←─── C_IC_NA_1 (GI, COT=10) ──────────│  Termination
  │                                        │
  └────── All Current Values Received ────┘
```

**COT Codes:**
- **COT=6**: Activation (command from client)
- **COT=7**: Activation Confirmation (RTU acknowledges)
- **COT=20**: Interrogated by Station Interrogation (GI response data)
- **COT=10**: Activation Termination (GI complete)

### 3. Spontaneous Transmission (New TFR Event)

When a new Transient Fault Record is generated (via REST API), the RTU spontaneously transmits updated values:

```
Client                                    RTU
  │                                        │
  │                                        │  [REST API: Create TFR]
  │                                        │  [Generator creates fault data]
  │                                        │
  │←─── M_ME_TF_1 (IOA 1100, COT=3) ─────│  Va Pre-Fault = 10.83 kV
  │←─── M_ME_TF_1 (IOA 1101, COT=3) ─────│  Vb Pre-Fault = 11.04 kV
  │←─── M_ME_TF_1 (IOA 1102, COT=3) ─────│  Vc Pre-Fault = 10.64 kV
  │←─── M_ME_TF_1 (IOA 1200, COT=3) ─────│  Va Fault = 1.09 kV
  │←─── M_ME_TF_1 (IOA 1201, COT=3) ─────│  Vb Fault = 1.12 kV
  │←─── M_ME_TF_1 (IOA 1202, COT=3) ─────│  Vc Fault = 1.05 kV
  │←─── M_ME_TF_1 (IOA 1203, COT=3) ─────│  Ia Fault = 3463.6 A
  │←─── M_ME_TF_1 (IOA 1204, COT=3) ─────│  Ib Fault = 3381.1 A
  │←─── M_ME_TF_1 (IOA 1205, COT=3) ─────│  Ic Fault = 3156.1 A
  │←─── M_SP_TB_1 (IOA 1301, COT=3) ─────│  Fault Active = FALSE (cleared)
  │                                        │
  └─────── New Fault Data Received ───────┘
```

**COT=3**: Spontaneous (unsolicited data transmission)

### 4. Clock Synchronization

RTU accepts time synchronization from the master:

```
Client                                    RTU
  │                                        │
  │──── C_CS_NA_1 (Clock Sync, COT=6) ──→│  Time: 2026-01-09 12:34:56
  │                                        │
  │←─── C_CS_NA_1 (Clock Sync, COT=7) ───│  ACK (Time accepted)
  │                                        │
  └────── RTU Clock Synchronized ─────────┘
```

## Typical SCADA Display Layout

```
╔═════════════════════════════════════════════════════════════════════════════╗
║  RTU - Synthetic TFR Generator                     Status: ● CONNECTED     ║
║  Common Address: 1                                 Last Update: 12:34:56   ║
╠═════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  PRE-FAULT MEASUREMENTS                    FAULT MEASUREMENTS              ║
║  ┌──────────────────────────┐             ┌──────────────────────────┐    ║
║  │ Phase A:  11.04 kV       │             │ Phase A:   1.09 kV       │    ║
║  │ Phase B:  10.83 kV       │             │ Phase B:   1.12 kV       │    ║
║  │ Phase C:  10.64 kV       │             │ Phase C:   1.05 kV       │    ║
║  │                          │             │                          │    ║
║  │ Phase A:   393 A         │             │ Phase A:  3464 A         │    ║
║  │ Phase B:   366 A         │             │ Phase B:  3381 A         │    ║
║  │ Phase C:   402 A         │             │ Phase C:  3156 A         │    ║
║  │                          │             │                          │    ║
║  │ Frequency: 50.02 Hz      │             │ Frequency: 49.80 Hz      │    ║
║  └──────────────────────────┘             └──────────────────────────┘    ║
║                                                                             ║
║  PROTECTION STATUS                                                          ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │ Circuit Breaker:  ● CLOSED                                          │  ║
║  │ Protection:       ● ARMED                                           │  ║
║  │ Fault Active:     ○ INACTIVE                                        │  ║
║  │                                                                      │  ║
║  │ Last Fault: THREE_PHASE_FAULT (2026-01-09 10:26:15)                │  ║
║  │ Duration: 118 ms                                                    │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                             ║
║  [Request General Interrogation]  [Export COMTRADE]  [View Details]       ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

## Integration with SCADA Systems

### Typical Use Cases

1. **Training Simulator**
   - Generate realistic fault scenarios for operator training
   - Pre-fault → Fault → Post-fault sequence visible in real-time
   - Protection operation timing observable

2. **Algorithm Testing**
   - Test fault detection algorithms
   - Verify protection relay coordination
   - Validate SCADA alarm processing

3. **System Integration Testing**
   - Verify IEC 104 protocol implementation
   - Test spontaneous transmission handling
   - Validate time synchronization

4. **Data Collection for Analysis**
   - Export COMTRADE files for offline analysis
   - Historical fault record database
   - Performance benchmarking

## Device Capabilities Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ SUPPORTED IEC 104 FEATURES                                      │
├─────────────────────────────────────────────────────────────────┤
│ ✓ General Interrogation (C_IC_NA_1)                            │
│ ✓ Spontaneous Transmission (COT=3)                             │
│ ✓ Clock Synchronization (C_CS_NA_1)                            │
│ ✓ Time-tagged measurements (M_ME_TF_1)                         │
│ ✓ Single point information (M_SP_TB_1)                         │
│ ✓ Double point information (M_DP_TB_1)                         │
│ ✓ Protection event recording (M_EP_TE_1, M_EP_TD_1)            │
│ ✓ Multiple concurrent client connections                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ DATA CHARACTERISTICS                                             │
├─────────────────────────────────────────────────────────────────┤
│ Total Information Objects:     17                               │
│ Analog Measurements:           14 (7 pre-fault + 7 fault)       │
│ Digital Status Points:         3                                │
│ Time Resolution:               Microseconds                      │
│ Update Method:                 Spontaneous on new TFR           │
│ Fault Types Supported:         10 predefined types              │
└─────────────────────────────────────────────────────────────────┘
```

## Example Client Configuration (Generic SCADA)

### Connection Settings
```
Protocol:       IEC 60870-5-104
Address:        rtu-server:2404
Common Address: 1
Timeout:        30 seconds
K-value:        12 (max unacknowledged I-frames)
W-value:        8 (acknowledgment after W I-frames)
T1:             15 seconds (timeout for send or test APDUs)
T2:             10 seconds (timeout for acknowledgments)
T3:             20 seconds (test frame timeout)
```

### Point Configuration Template
```csv
IOA,Type,Description,Unit,Scaling,Deadband
1100,M_ME_TF_1,Pre-Fault Va,kV,1.0,0.1
1101,M_ME_TF_1,Pre-Fault Vb,kV,1.0,0.1
1102,M_ME_TF_1,Pre-Fault Vc,kV,1.0,0.1
1103,M_ME_TF_1,Pre-Fault Ia,A,1.0,1.0
1104,M_ME_TF_1,Pre-Fault Ib,A,1.0,1.0
1105,M_ME_TF_1,Pre-Fault Ic,A,1.0,1.0
1106,M_ME_TF_1,Pre-Fault Freq,Hz,1.0,0.01
1200,M_ME_TF_1,Fault Va,kV,1.0,0.1
1201,M_ME_TF_1,Fault Vb,kV,1.0,0.1
1202,M_ME_TF_1,Fault Vc,kV,1.0,0.1
1203,M_ME_TF_1,Fault Ia,A,1.0,1.0
1204,M_ME_TF_1,Fault Ib,A,1.0,1.0
1205,M_ME_TF_1,Fault Ic,A,1.0,1.0
1206,M_ME_TF_1,Fault Freq,Hz,1.0,0.01
1300,M_DP_TB_1,Breaker Position,state,1.0,0
1301,M_SP_TB_1,Fault Active,bool,1.0,0
1302,M_SP_TB_1,Protection Armed,bool,1.0,0
```

## Comparison with Real RTU

### Similar to Real RTU:
- ✓ Standard IEC 104 protocol compliance
- ✓ Realistic voltage/current measurements
- ✓ Protection event sequences
- ✓ Time-tagged data points
- ✓ Spontaneous transmission on events
- ✓ Multiple client support

### Differences from Real RTU:
- ✗ Synthetic data (not from actual field equipment)
- ✗ Fixed IOA mapping (not configurable)
- ✗ Simplified protection logic
- ✗ No control commands (read-only device)
- ✗ No analog/digital input modules
- ✗ REST API for data generation (not typical for field RTUs)

## Summary

From an IEC 60870-5-104 perspective, this device appears as:

**A Remote Terminal Unit (RTU)** that provides:
- Real-time electrical measurements (voltages, currents, frequency)
- Protection system status and events
- Pre-fault and fault condition data
- Standard IEC 104 protocol communication
- Spontaneous updates when new fault records are available

The device is **read-only** - it reports measurements but does not accept control commands. It's designed for **training, testing, and integration purposes** rather than actual power system control.
