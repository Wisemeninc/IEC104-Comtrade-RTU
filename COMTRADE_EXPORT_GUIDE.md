# TFR Export Guide - COMTRADE Format

## Overview

The RTU supports exporting Transient Fault Records (TFR) in **COMTRADE (IEEE C37.111-2013)** format, the industry standard for power system fault data exchange.

## What is COMTRADE?

COMTRADE (Common Format for Transient Data Exchange) is an IEEE standard that defines a file format for storing power system transient data. It's widely supported by:
- Protection relay analysis software (SEL, GE, ABB, Siemens)
- Power system simulation tools (PSCAD, EMTP, DIgSILENT PowerFactory)
- Fault analysis and visualization tools
- SCADA/EMS systems

## File Structure

Each COMTRADE record consists of 3 files:

### 1. Configuration File (.cfg)
Defines the structure of the data:
- Station and device identification
- Number and type of channels (analog/digital)
- Channel names, units, and scaling factors
- Sampling rate and total samples
- Trigger time and date
- Data format (ASCII or Binary)

### 2. Data File (.dat)
Contains time-stamped sample data:
- Sample number
- Timestamp (microseconds)
- Analog channel values (voltages, currents, frequency)
- Digital channel states (breaker status, protection flags)

### 3. Header File (.hdr)
Optional human-readable metadata:
- Fault type and description
- Pre-fault, fault, and post-fault conditions
- Event timeline (pickup, trip, breaker operation)
- Channel descriptions
- Export information

## Exported Channels

### Analog Channels (7)
1. **Va** - Phase A Voltage (kV)
2. **Vb** - Phase B Voltage (kV)
3. **Vc** - Phase C Voltage (kV)
4. **Ia** - Phase A Current (A)
5. **Ib** - Phase B Current (A)
6. **Ic** - Phase C Current (A)
7. **Freq** - System Frequency (Hz)

### Digital Channels (5)
1. **BKR_52** - Circuit Breaker Status (1=closed, 0=open)
2. **FAULT_ACT** - Fault Active Flag (1=active, 0=cleared)
3. **PROT_ARM** - Protection Armed (1=armed, 0=disarmed)
4. **TRIP_CMD** - Trip Command Issued (1=active, 0=inactive)
5. **PICKUP** - Protection Pickup (1=detected, 0=normal)

## Export Methods

### 1. Single TFR Export

Export a specific TFR by ID:

```bash
# Basic export (default 4000 Hz sampling)
curl -o tfr_001.zip "http://localhost:8080/api/tfr/1/comtrade"

# Custom sampling rate (1000-16000 Hz)
curl -o tfr_001.zip "http://localhost:8080/api/tfr/1/comtrade?sample_rate=8000"

# Extract files
unzip tfr_001.zip
```

Output files:
```
TFR_0001_THREE_PHASE_FAULT_20260109_123456.cfg
TFR_0001_THREE_PHASE_FAULT_20260109_123456.dat
TFR_0001_THREE_PHASE_FAULT_20260109_123456.hdr
```

### 2. Batch Export

Export all TFRs at once:

```bash
# Export up to 100 TFRs
curl -o all_tfrs.zip "http://localhost:8080/api/tfr/export/comtrade/batch"

# Specify limit and sampling rate
curl -o all_tfrs.zip "http://localhost:8080/api/tfr/export/comtrade/batch?limit=50&sample_rate=4000"

# Extract - each TFR in its own folder
unzip all_tfrs.zip
```

Output structure:
```
TFR_Batch_20260109_123456.zip
├── TFR_0001/
│   ├── TFR_0001_THREE_PHASE_FAULT_20260109_123456.cfg
│   ├── TFR_0001_THREE_PHASE_FAULT_20260109_123456.dat
│   └── TFR_0001_THREE_PHASE_FAULT_20260109_123456.hdr
├── TFR_0002/
│   ├── TFR_0002_LINE_TO_LINE_AB_20260109_123457.cfg
│   ├── TFR_0002_LINE_TO_LINE_AB_20260109_123457.dat
│   └── TFR_0002_LINE_TO_LINE_AB_20260109_123457.hdr
└── ...
```

### 3. Automated Export Script

Create a script for regular exports:

```bash
#!/bin/bash
# export_daily_tfrs.sh

DATE=$(date +%Y%m%d)
OUTPUT_DIR="/data/tfr_exports/$DATE"
mkdir -p "$OUTPUT_DIR"

# Get total TFR count
TOTAL=$(curl -s "http://localhost:8080/api/tfr/list?page=1&page_size=1" | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")

echo "Exporting $TOTAL TFRs for $DATE..."

# Export batch
curl -o "$OUTPUT_DIR/tfrs_$DATE.zip" \
     "http://localhost:8080/api/tfr/export/comtrade/batch?limit=$TOTAL"

echo "Export complete: $OUTPUT_DIR/tfrs_$DATE.zip"
```

## Sampling Rate Guidelines

| Sample Rate | Samples/Cycle (50Hz) | Use Case |
|-------------|---------------------|----------|
| 1000 Hz     | 20 | Basic fault analysis |
| 2000 Hz     | 40 | Standard protection studies |
| 4000 Hz     | 80 | **Default** - Detailed waveform analysis |
| 8000 Hz     | 160 | High-resolution fault studies |
| 16000 Hz    | 320 | Research/advanced analysis |

**Recommendation:** Use 4000 Hz (80 samples/cycle) for standard analysis. Higher rates increase file size without significant benefit for most applications.

## Data Quality

The exported COMTRADE files contain:

✓ **Time-stamped waveforms** with microsecond precision  
✓ **Pre-fault steady-state** data (100ms before fault)  
✓ **Fault transient** data with realistic voltage sags and current surges  
✓ **Post-fault recovery** data (100ms after clearing)  
✓ **Protection event sequence** (pickup → trip → breaker operation)  
✓ **Digital status changes** synchronized with analog data  

## Viewing COMTRADE Files

### Software Tools

**Commercial:**
- SEL AcSELerator Analytic Assistant
- GE EnerVista Viewpoint
- ABB PCM600
- Siemens SIGRA Viewer
- OMICRON CMView

**Open Source/Free:**
- Python: `comtrade` library
- MATLAB: COMTRADE Reader toolbox
- Online viewers: Various web-based tools

### Python Example

```python
import comtrade

# Load COMTRADE file
rec = comtrade.load("TFR_0001_THREE_PHASE_FAULT_20260109_123456.cfg")

# Access data
print(f"Total samples: {rec.total_samples}")
print(f"Sampling rate: {rec.frequency} Hz")

# Get analog channel data
va = rec.analog[0]  # Phase A voltage
ia = rec.analog[3]  # Phase A current

# Plot waveforms
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.subplot(2, 1, 1)
plt.plot(rec.time, va)
plt.title("Phase A Voltage")
plt.ylabel("Voltage (kV)")
plt.subplot(2, 1, 2)
plt.plot(rec.time, ia)
plt.title("Phase A Current")
plt.ylabel("Current (A)")
plt.xlabel("Time (s)")
plt.tight_layout()
plt.show()
```

## Integration with Analysis Systems

### SCADA/EMS Integration

```python
# Automated TFR retrieval for SCADA integration
import requests
import time

RTU_URL = "http://rtu-server:8080"

def monitor_for_new_tfrs():
    last_id = 0
    
    while True:
        # Check for new TFRs
        resp = requests.get(f"{RTU_URL}/api/tfr/list?page=1&page_size=1")
        data = resp.json()
        
        if data['records']:
            latest_id = data['records'][0]['id']
            
            if latest_id > last_id:
                # New TFR detected - export to COMTRADE
                print(f"New TFR detected: {latest_id}")
                
                # Download COMTRADE export
                comtrade_resp = requests.get(
                    f"{RTU_URL}/api/tfr/{latest_id}/comtrade",
                    stream=True
                )
                
                # Save to analysis system
                with open(f"/analysis/tfr_{latest_id:04d}.zip", 'wb') as f:
                    f.write(comtrade_resp.content)
                
                last_id = latest_id
        
        time.sleep(10)  # Check every 10 seconds
```

## File Naming Convention

Format: `TFR_{ID}_{FAULT_TYPE}_{TIMESTAMP}.{ext}`

Example: `TFR_0042_SINGLE_PHASE_TO_GROUND_A_20260109_143522.cfg`

- **ID**: Zero-padded TFR identifier (4 digits)
- **FAULT_TYPE**: Descriptive fault classification
- **TIMESTAMP**: YYYYMMdd_HHmmss format
- **ext**: cfg, dat, or hdr

## Troubleshooting

### Large File Sizes

If batch exports are too large:
- Reduce `limit` parameter
- Lower `sample_rate` (2000 Hz still provides good detail)
- Export in smaller batches by date range

### Missing Data

If COMTRADE files appear incomplete:
- Verify TFR was fully generated (check `/api/tfr/{id}` status)
- Ensure adequate sampling rate for fault duration
- Check server logs for export errors

### Compatibility Issues

If analysis software rejects files:
- Verify software supports IEEE C37.111-2013
- Try ASCII format (default) vs Binary
- Check for special character issues in filenames

## Standards Compliance

This implementation follows:
- **IEEE C37.111-2013**: COMTRADE file format standard
- **IEC 60870-5-104**: Protocol for real-time data transmission
- **Power system conventions**: Phase naming (A-B-C), voltage/current units

## Support

For issues or questions:
1. Check API documentation: `/docs` (Swagger UI)
2. Review server logs: `docker compose logs`
3. Test with simple export first: Single TFR at 4000 Hz
