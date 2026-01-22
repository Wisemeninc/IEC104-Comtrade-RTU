#!/usr/bin/env python3
"""
IEC 104 Client to inspect RTU data points and structure.
Shows how the device appears from a SCADA/control system perspective.
"""
import c104
import time
import sys

def inspect_rtu():
    """Connect to RTU and inspect its IEC 104 configuration"""
    
    print("=" * 80)
    print("IEC 60870-5-104 RTU INSPECTION")
    print("=" * 80)
    print()
    
    try:
        # Create client
        print("1. Creating IEC 104 client...")
        client = c104.Client()
        
        # Add connection to RTU
        print("2. Connecting to RTU at localhost:2404...")
        connection = client.add_connection(ip="localhost", port=2404, init=c104.Init.INTERROGATION)
        
        # Add station (common address 1)
        print("3. Adding station with common address 1...")
        station = connection.add_station(common_address=1)
        
        print()
        print("=" * 80)
        print("ADDING DATA POINTS (Information Objects)")
        print("=" * 80)
        print()
        
        # Add monitoring points for all IOAs
        points = {}
        
        # Pre-fault measurements (M_ME_TF_1 - Measured value, short floating point with time)
        print("PRE-FAULT MEASUREMENTS (IOA 1100-1106):")
        print("-" * 80)
        prefault_channels = [
            (1100, "Va_PreFault", "Phase A Voltage (Pre-Fault)", "kV"),
            (1101, "Vb_PreFault", "Phase B Voltage (Pre-Fault)", "kV"),
            (1102, "Vc_PreFault", "Phase C Voltage (Pre-Fault)", "kV"),
            (1103, "Ia_PreFault", "Phase A Current (Pre-Fault)", "A"),
            (1104, "Ib_PreFault", "Phase B Current (Pre-Fault)", "A"),
            (1105, "Ic_PreFault", "Phase C Current (Pre-Fault)", "A"),
            (1106, "Freq_PreFault", "Frequency (Pre-Fault)", "Hz"),
        ]
        
        for ioa, name, desc, unit in prefault_channels:
            point = station.add_point(io_address=ioa, type=c104.Type.M_ME_TF_1)
            points[ioa] = {"name": name, "desc": desc, "unit": unit, "point": point}
            print(f"  IOA {ioa:4d}: {desc:40s} [{unit}]")
        
        print()
        
        # Fault measurements (M_ME_TF_1)
        print("FAULT MEASUREMENTS (IOA 1200-1206):")
        print("-" * 80)
        fault_channels = [
            (1200, "Va_Fault", "Phase A Voltage (Fault)", "kV"),
            (1201, "Vb_Fault", "Phase B Voltage (Fault)", "kV"),
            (1202, "Vc_Fault", "Phase C Voltage (Fault)", "kV"),
            (1203, "Ia_Fault", "Phase A Current (Fault)", "A"),
            (1204, "Ib_Fault", "Phase B Current (Fault)", "A"),
            (1205, "Ic_Fault", "Phase C Current (Fault)", "A"),
            (1206, "Freq_Fault", "Frequency (Fault)", "Hz"),
        ]
        
        for ioa, name, desc, unit in fault_channels:
            point = station.add_point(io_address=ioa, type=c104.Type.M_ME_TF_1)
            points[ioa] = {"name": name, "desc": desc, "unit": unit, "point": point}
            print(f"  IOA {ioa:4d}: {desc:40s} [{unit}]")
        
        print()
        
        # Status points
        print("STATUS/DIGITAL POINTS (IOA 1300-1302):")
        print("-" * 80)
        status_channels = [
            (1300, "Breaker_Pos", "Circuit Breaker Position", "M_DP_TB_1", "state"),
            (1301, "Fault_Active", "Fault Active Flag", "M_SP_TB_1", "bool"),
            (1302, "Prot_Armed", "Protection Armed", "M_SP_TB_1", "bool"),
        ]
        
        for ioa, name, desc, point_type, unit in status_channels:
            if point_type == "M_DP_TB_1":
                point = station.add_point(io_address=ioa, type=c104.Type.M_DP_TB_1)
            else:
                point = station.add_point(io_address=ioa, type=c104.Type.M_SP_TB_1)
            points[ioa] = {"name": name, "desc": desc, "unit": unit, "point": point}
            print(f"  IOA {ioa:4d}: {desc:40s} [{point_type}]")
        
        print()
        print("=" * 80)
        print("CONNECTING TO RTU")
        print("=" * 80)
        print()
        
        # Start connection
        connection.start()
        print("✓ Connection established")
        time.sleep(1)
        
        # Check connection status
        if connection.is_connected:
            print(f"✓ Connected to RTU")
            print(f"  State: {connection.state}")
        else:
            print("✗ Failed to connect")
            return
        
        print()
        print("=" * 80)
        print("SENDING GENERAL INTERROGATION (GI)")
        print("=" * 80)
        print()
        
        # Send General Interrogation
        print("Sending GI command (COT=6) - requesting all data points...")
        station.interrogation(cause=c104.Cot.ACTIVATION)
        
        # Wait for responses
        print("Waiting for GI responses...")
        time.sleep(3)
        
        print()
        print("=" * 80)
        print("CURRENT RTU STATE (After General Interrogation)")
        print("=" * 80)
        print()
        
        # Read all point values
        print("PRE-FAULT MEASUREMENTS:")
        print("-" * 80)
        for ioa in range(1100, 1107):
            if ioa in points:
                p = points[ioa]
                try:
                    value = p["point"].value
                    print(f"  {p['desc']:45s}: {value:10.3f} {p['unit']}")
                except Exception as e:
                    print(f"  {p['desc']:45s}: [Not available]")
        
        print()
        print("FAULT MEASUREMENTS:")
        print("-" * 80)
        for ioa in range(1200, 1207):
            if ioa in points:
                p = points[ioa]
                try:
                    value = p["point"].value
                    print(f"  {p['desc']:45s}: {value:10.3f} {p['unit']}")
                except Exception as e:
                    print(f"  {p['desc']:45s}: [Not available]")
        
        print()
        print("STATUS POINTS:")
        print("-" * 80)
        for ioa in range(1300, 1303):
            if ioa in points:
                p = points[ioa]
                try:
                    value = p["point"].value
                    if ioa == 1300:
                        # Double point: 0=intermediate, 1=off, 2=on
                        status = {0: "INTERMEDIATE", 1: "OFF/OPEN", 2: "ON/CLOSED"}.get(value, "UNKNOWN")
                        print(f"  {p['desc']:45s}: {status} ({value})")
                    else:
                        # Single point: 0=inactive, 1=active
                        status = "ACTIVE" if value else "INACTIVE"
                        print(f"  {p['desc']:45s}: {status} ({value})")
                except Exception as e:
                    print(f"  {p['desc']:45s}: [Not available]")
        
        print()
        print("=" * 80)
        print("DEVICE CHARACTERISTICS")
        print("=" * 80)
        print()
        print("Connection Parameters:")
        print(f"  Protocol: IEC 60870-5-104")
        print(f"  IP Address: localhost")
        print(f"  Port: 2404")
        print(f"  Common Address: 1")
        print(f"  Connection State: {connection.state}")
        print()
        print("Device Type:")
        print(f"  Function: Remote Terminal Unit (RTU)")
        print(f"  Purpose: Synthetic Transient Fault Record Generator")
        print(f"  Manufacturer: Python RTU Simulator")
        print()
        print("Data Points Summary:")
        print(f"  Total Information Objects: {len(points)}")
        print(f"  Analog Channels (M_ME_TF_1): 14")
        print(f"  Digital Channels (M_SP_TB_1): 2")
        print(f"  Double Point (M_DP_TB_1): 1")
        print()
        print("Capabilities:")
        print(f"  ✓ General Interrogation (GI)")
        print(f"  ✓ Spontaneous Transmission (COT=3)")
        print(f"  ✓ Time-tagged values")
        print(f"  ✓ Pre-fault and fault measurements")
        print(f"  ✓ Protection event recording")
        print()
        print("=" * 80)
        print()
        
        # Monitor for spontaneous updates
        print("Monitoring for spontaneous updates for 10 seconds...")
        print("(Create a new TFR via REST API to see spontaneous transmission)")
        print()
        
        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
        
        print()
        print()
        print("=" * 80)
        print("DISCONNECTING")
        print("=" * 80)
        print()
        
        connection.stop()
        print("✓ Connection closed")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print()
    print("=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(inspect_rtu())
