# IEC 104 COMTRADE Availability Signals

## Overview

This RTU signals COMTRADE file availability through the existing **IEC 60870-5-104 protocol** using spontaneous data transmission. When a COMTRADE export is generated, the RTU automatically sends IEC 104 data points to inform connected SCADA/clients that the file is ready for download.

This approach keeps all communication within the industrial standard protocol, avoiding the need for separate webhook infrastructure.

---

## IEC 104 Signal Points

### New IOA Addresses (1500-1502)

| IOA  | Type | Description | Values |
|------|------|-------------|--------|
| **1500** | `M_SP_TB_1` (Single Point with Time) | **COMTRADE Available Flag** | 0=No file available<br>1=COMTRADE ready for download |
| **1501** | `M_ME_NC_1` (Short Floating Point) | **TFR ID** | TFR ID number for which COMTRADE is available |
| **1502** | `M_ME_NC_1` (Short Floating Point) | **File Count** | Total number of COMTRADE files available in system |

---

## Protocol Behavior

### Sequence of Events

1. **Fault Occurs** → TFR created → IEC 104 spontaneous transmission (COT=3) sends fault measurements
2. **COMTRADE Export Requested** → Client calls `/api/tfr/{id}/comtrade`
3. **COMTRADE Generated** → ZIP file created
4. **Spontaneous Signal** → IEC 104 sends:
   - IOA 1500 = `True` (COMTRADE available)
   - IOA 1501 = `42.0` (TFR ID)
   - IOA 1502 = `5.0` (total COMTRADE files available)

### Cause of Transmission

All COMTRADE availability signals use **COT=3 (Spontaneous)** to immediately notify clients without waiting for General Interrogation.

---

## Client Integration Examples

### Example 1: Python with c104 Library

```python
import c104

# Create IEC 104 client
client = c104.Client()
connection = client.add_connection(ip="192.168.1.100", port=2404)
station = connection.add_station(common_address=1)

# Add COMTRADE availability points
comtrade_available = station.add_point(
    io_address=1500,
    type=c104.Type.M_SP_TB_1
)
comtrade_tfr_id = station.add_point(
    io_address=1501,
    type=c104.Type.M_ME_NC_1
)
comtrade_file_count = station.add_point(
    io_address=1502,
    type=c104.Type.M_ME_NC_1
)

# Define callback for spontaneous updates
def on_comtrade_signal(point: c104.Point):
    """Handle COMTRADE availability signal"""
    if point.io_address == 1500 and point.value:
        print(f"COMTRADE file available!")
        
        # Get TFR ID from IOA 1501
        tfr_id_point = station.get_point(1501)
        tfr_id = int(tfr_id_point.value)
        
        print(f"Downloading COMTRADE for TFR {tfr_id}...")
        download_comtrade(tfr_id)

# Register callback
comtrade_available.on_receive(on_comtrade_signal)

# Connect and start
connection.start()
print("Monitoring for COMTRADE availability signals...")
```

### Example 2: Download COMTRADE on Signal

```python
import requests
import c104

def download_comtrade(tfr_id: int, rtu_web_api: str = "http://192.168.1.100:8080"):
    """Download COMTRADE file when signaled via IEC 104"""
    url = f"{rtu_web_api}/api/tfr/{tfr_id}/comtrade"
    
    response = requests.get(url, params={"sample_rate": 4000})
    
    if response.status_code == 200:
        filename = f"TFR_{tfr_id:04d}.zip"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download COMTRADE for TFR {tfr_id}")

def on_comtrade_available(point: c104.Point):
    """Callback when COMTRADE availability signal received"""
    if point.value:  # COMTRADE is available
        # Read TFR ID from IOA 1501
        tfr_id = int(station.get_point(1501).value)
        download_comtrade(tfr_id)

# Set up IEC 104 client
client = c104.Client()
connection = client.add_connection(ip="192.168.1.100", port=2404)
station = connection.add_station(common_address=1)

# Monitor COMTRADE availability
comtrade_point = station.add_point(io_address=1500, type=c104.Type.M_SP_TB_1)
comtrade_point.on_receive(on_comtrade_available)

station.add_point(io_address=1501, type=c104.Type.M_ME_NC_1)  # TFR ID

connection.start()
```

### Example 3: General Interrogation Response

```python
def handle_general_interrogation():
    """
    Process GI response to check if any COMTRADE files are available
    """
    # Send GI command
    station.interrogation()
    
    # Wait for response
    time.sleep(1)
    
    # Check COMTRADE availability
    comtrade_available = station.get_point(1500)
    if comtrade_available.value:
        tfr_id = int(station.get_point(1501).value)
        file_count = int(station.get_point(1502).value)
        
        print(f"COMTRADE available for TFR {tfr_id}")
        print(f"Total COMTRADE files in system: {file_count}")
```

---

## Advantages of IEC 104 Signaling

### 1. **Native Protocol Integration**
- No additional infrastructure required (no webhook servers)
- All communication over existing IEC 104 connection
- Leverages existing firewall rules and security policies

### 2. **Standardized Industrial Protocol**
- IEC 60870-5-104 is the industry standard for SCADA communication
- Compatible with all IEC 104 clients and SCADA systems
- Well-understood by power system engineers

### 3. **Reliable Delivery**
- Built-in acknowledgment at IEC 104 protocol level
- Connection-oriented TCP ensures delivery
- Clients automatically receive updates when connected

### 4. **Real-Time Notification**
- Spontaneous transmission (COT=3) provides immediate notification
- No polling required
- Sub-second latency from generation to client notification

### 5. **Stateful and Queryable**
- Clients can query availability via General Interrogation (GI)
- Persistent state - reconnecting clients see current availability
- File count indicates total COMTRADE files in system

---

## Use Cases

### Use Case 1: Automated Fault Analysis System

```python
# SCADA system monitors for faults and automatically downloads COMTRADE
class FaultAnalysisSystem:
    def __init__(self):
        self.iec104_client = setup_iec104_client()
        self.pending_analysis = []
    
    def on_fault_detected(self, tfr_data):
        """Fault detected via IEC 104 spontaneous transmission"""
        tfr_id = tfr_data['tfr_id']
        self.pending_analysis.append(tfr_id)
        print(f"Fault detected: TFR {tfr_id}, waiting for COMTRADE...")
    
    def on_comtrade_ready(self, tfr_id):
        """COMTRADE availability signaled via IEC 104"""
        if tfr_id in self.pending_analysis:
            print(f"COMTRADE ready for TFR {tfr_id}, downloading...")
            comtrade_file = download_comtrade(tfr_id)
            
            # Analyze fault waveform
            analysis_result = analyze_fault_waveform(comtrade_file)
            
            # Update outage management system
            update_oms(tfr_id, analysis_result)
            
            self.pending_analysis.remove(tfr_id)
```

### Use Case 2: Archive System

```python
# Automatically archive all COMTRADE files to long-term storage
def comtrade_archiver():
    """Monitor for COMTRADE signals and archive files"""
    archived_tfr_ids = load_archived_list()
    
    while True:
        # Check for new COMTRADE availability
        comtrade_point = station.get_point(1500)
        tfr_id_point = station.get_point(1501)
        
        if comtrade_point.value:
            tfr_id = int(tfr_id_point.value)
            
            if tfr_id not in archived_tfr_ids:
                # Download and archive
                comtrade_file = download_comtrade(tfr_id)
                archive_to_storage(comtrade_file, tfr_id)
                archived_tfr_ids.add(tfr_id)
                print(f"Archived COMTRADE for TFR {tfr_id}")
        
        time.sleep(5)  # Check every 5 seconds
```

### Use Case 3: Event-Driven Dashboard

```python
# Real-time dashboard showing COMTRADE availability
class DashboardUpdater:
    def __init__(self, websocket_clients):
        self.websocket_clients = websocket_clients
        self.setup_iec104_monitoring()
    
    def on_comtrade_signal(self, point):
        """Forward IEC 104 signal to web dashboard clients"""
        if point.io_address == 1500 and point.value:
            tfr_id = int(station.get_point(1501).value)
            file_count = int(station.get_point(1502).value)
            
            # Broadcast to all connected dashboard clients
            notification = {
                "type": "comtrade_available",
                "tfr_id": tfr_id,
                "file_count": file_count,
                "timestamp": datetime.now().isoformat()
            }
            
            for client in self.websocket_clients:
                client.send_json(notification)
```

---

## Testing

### Manual Test: Create Fault and Export COMTRADE

```bash
# Terminal 1: Monitor IEC 104 traffic
python inspect_iec104.py --monitor-ioa 1500,1501,1502

# Terminal 2: Create fault and export COMTRADE
curl -X POST http://localhost:8080/api/tfr/create \
  -H "Content-Type: application/json" \
  -d '{"fault_type": "THREE_PHASE_FAULT"}'

curl -o tfr_001.zip "http://localhost:8080/api/tfr/1/comtrade"

# Terminal 1 should show:
# Spontaneous Update (COT=3):
#   IOA 1500: True (COMTRADE Available)
#   IOA 1501: 1.0 (TFR ID)
#   IOA 1502: 1.0 (File Count)
```

### Automated Test Script

```python
import c104
import time

# Connect to RTU
client = c104.Client()
connection = client.add_connection(ip="localhost", port=2404)
station = connection.add_station(common_address=1)

# Track signals received
signals_received = []

def on_spontaneous(point):
    if point.io_address in [1500, 1501, 1502]:
        signals_received.append({
            "ioa": point.io_address,
            "value": point.value,
            "timestamp": time.time()
        })
        print(f"Received: IOA {point.io_address} = {point.value}")

# Add points and register callback
for ioa in [1500, 1501, 1502]:
    point = station.add_point(io_address=ioa, type=c104.Type.M_ME_NC_1)
    point.on_receive(on_spontaneous)

# Connect
connection.start()
time.sleep(2)

print("Monitoring for COMTRADE signals...")
print("Trigger COMTRADE export via web API to see signals")

# Wait for signals
time.sleep(60)

# Verify signals received
if len(signals_received) >= 3:
    print("✓ Test passed: Received COMTRADE availability signals")
else:
    print("✗ Test failed: Did not receive expected signals")
```

---

## Status Monitoring

Check COMTRADE availability status via REST API:

```bash
curl http://localhost:8080/api/status
```

Response includes COMTRADE tracking:
```json
{
  "iec104_port": 2404,
  "iec104_connected_clients": 2,
  "web_port": 8080,
  "comtrade_available_count": 5,
  "latest_comtrade_tfr_id": 42
}
```

---

## IOA Mapping Summary

Complete IOA address map including COMTRADE signals:

| IOA Range | Type | Description |
|-----------|------|-------------|
| 1000-1009 | Protection Events | Fault detection, trip commands |
| 1100-1106 | Pre-Fault Measurements | Va, Vb, Vc, Ia, Ib, Ic, Freq |
| 1200-1206 | Fault Measurements | Va, Vb, Vc, Ia, Ib, Ic, Freq |
| 1300-1302 | Status Points | Breaker, Fault Active, Protection Armed |
| 1400 | Device Clock | System time |
| **1500-1502** | **COMTRADE Signals** | **Availability, TFR ID, File Count** |

---

## Comparison with Webhook Approach

| Feature | IEC 104 Signals | Webhooks |
|---------|-----------------|----------|
| **Protocol** | IEC 60870-5-104 (industrial standard) | HTTP/HTTPS (IT standard) |
| **Infrastructure** | Uses existing SCADA connection | Requires web server endpoint |
| **Firewall** | Already configured for IEC 104 | Requires outbound HTTPS rules |
| **Reliability** | TCP with protocol-level ACK | Retry logic needed |
| **Security** | IEC 104 authentication | OAuth2/JWT/API keys |
| **Integration** | Native to SCADA systems | Requires webhook receiver |
| **Latency** | Sub-second (spontaneous) | Sub-second (async) |
| **State Query** | General Interrogation | Requires API call |
| **Industry Fit** | ✓ Standard for substations | ○ Common in IT systems |

**Recommendation**: IEC 104 signaling is more appropriate for traditional SCADA environments, while webhooks are better for cloud-native or hybrid architectures.

---

## References

- **IEC 60870-5-104** - Telecontrol equipment and systems, Part 5-104: Transmission protocols
- **IEC 60870-5-101** - Companion standard for basic telecontrol tasks
- **IEEE C37.111-2013** - COMTRADE file format standard
- [lib60870 Documentation](https://github.com/mz-automation/lib60870) - IEC 104 implementation
