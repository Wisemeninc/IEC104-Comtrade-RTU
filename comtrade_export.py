"""
COMTRADE (IEEE C37.111) format export for transient fault records.
Generates .cfg, .dat, and .hdr files for TFR analysis.
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import struct
from models import TFRDetail, ProtectionEvent


class ComtradeExporter:
    """Export TFR data to COMTRADE format (IEEE C37.111-2013)"""
    
    def __init__(self, tfr: TFRDetail, sample_rate: int = 4000):
        """
        Initialize COMTRADE exporter.
        
        Args:
            tfr: Transient fault record to export
            sample_rate: Sampling rate in Hz (default 4000 = 80 samples/cycle @ 50Hz)
        """
        self.tfr = tfr
        self.sample_rate = sample_rate
        self.samples_per_cycle = sample_rate // 50  # Assuming 50Hz system
        
        # Calculate total duration and samples
        self.duration_seconds = (tfr.duration_ms + 300) / 1000.0  # Add 150ms before + 150ms after
        self.total_samples = int(self.duration_seconds * sample_rate)
        
        # Station and equipment info
        self.station_name = "RTU_SIM"
        self.rec_dev_id = "PYTHON_RTU"
        self.rev_year = 2013  # COMTRADE standard revision
        
    def export(self, output_dir: str, base_filename: str) -> Dict[str, str]:
        """
        Export TFR to COMTRADE format files.
        
        Args:
            output_dir: Directory to write files
            base_filename: Base name for output files (without extension)
        
        Returns:
            Dictionary with paths to generated files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        cfg_file = os.path.join(output_dir, f"{base_filename}.cfg")
        dat_file = os.path.join(output_dir, f"{base_filename}.dat")
        hdr_file = os.path.join(output_dir, f"{base_filename}.hdr")
        
        # Generate files
        self._write_cfg_file(cfg_file)
        self._write_dat_file(dat_file)
        self._write_hdr_file(hdr_file)
        
        return {
            "cfg": cfg_file,
            "dat": dat_file,
            "hdr": hdr_file,
            "base": base_filename
        }
    
    def _write_cfg_file(self, filepath: str):
        """Write COMTRADE configuration file (.cfg)"""
        with open(filepath, 'w') as f:
            # Line 1: Station name, recording device ID, COMTRADE revision year
            f.write(f"{self.station_name},{self.rec_dev_id},{self.rev_year}\n")
            
            # Line 2: Number of channels (TT = total, ##A = analog, ##D = digital)
            num_analog = 7  # Va, Vb, Vc, Ia, Ib, Ic, Freq
            num_digital = 5  # Breaker, Fault_Active, Protection_Armed, Trip, Pickup
            f.write(f"{num_analog + num_digital},{num_analog}A,{num_digital}D\n")
            
            # Analog channel definitions (Line 3 onwards)
            # Format: An,ch_id,ph,ccbm,uu,a,b,skew,min,max,primary,secondary,PS
            analog_channels = [
                (1, "Va", "A", "", "kV", 1.0, 0.0, 0.0, -20.0, 20.0, 11.0, 11.0, "P"),
                (2, "Vb", "B", "", "kV", 1.0, 0.0, 0.0, -20.0, 20.0, 11.0, 11.0, "P"),
                (3, "Vc", "C", "", "kV", 1.0, 0.0, 0.0, -20.0, 20.0, 11.0, 11.0, "P"),
                (4, "Ia", "A", "", "A", 1.0, 0.0, 0.0, -5000.0, 5000.0, 400.0, 400.0, "P"),
                (5, "Ib", "B", "", "A", 1.0, 0.0, 0.0, -5000.0, 5000.0, 400.0, 400.0, "P"),
                (6, "Ic", "C", "", "A", 1.0, 0.0, 0.0, -5000.0, 5000.0, 400.0, 400.0, "P"),
                (7, "Freq", "", "", "Hz", 1.0, 0.0, 0.0, 45.0, 55.0, 50.0, 50.0, "P"),
            ]
            
            for ch in analog_channels:
                f.write(f"{ch[0]},{ch[1]},{ch[2]},{ch[3]},{ch[4]},{ch[5]},{ch[6]},{ch[7]},{ch[8]},{ch[9]},{ch[10]},{ch[11]},{ch[12]}\n")
            
            # Digital channel definitions
            # Format: Dn,ch_id,ph,ccbm,y
            digital_channels = [
                (1, "BKR_52", "", "", 0),  # Breaker status (0=open, 1=closed)
                (2, "FAULT_ACT", "", "", 0),  # Fault active flag
                (3, "PROT_ARM", "", "", 1),  # Protection armed
                (4, "TRIP_CMD", "", "", 0),  # Trip command
                (5, "PICKUP", "", "", 0),  # Protection pickup
            ]
            
            for ch in digital_channels:
                f.write(f"{ch[0]},{ch[1]},{ch[2]},{ch[3]},{ch[4]}\n")
            
            # Line frequency
            f.write(f"50.0\n")
            
            # Number of sampling rates
            f.write(f"1\n")
            
            # Sampling rate and number of samples
            f.write(f"{self.sample_rate},{self.total_samples}\n")
            
            # Start date and time (pre-fault by 150ms)
            start_time = self.tfr.pre_fault.timestamp - timedelta(milliseconds=100)
            f.write(f"{start_time.strftime('%d/%m/%Y,%H:%M:%S')}.{start_time.microsecond:06d}\n")
            
            # Trigger date and time (fault inception)
            trigger_time = self.tfr.fault.timestamp
            f.write(f"{trigger_time.strftime('%d/%m/%Y,%H:%M:%S')}.{trigger_time.microsecond:06d}\n")
            
            # Data file type (ASCII or BINARY)
            f.write(f"ASCII\n")
            
            # Time multiplier (1.0 = microseconds)
            f.write(f"1.0\n")
    
    def _write_dat_file(self, filepath: str):
        """Write COMTRADE data file (.dat) in ASCII format"""
        start_time = self.tfr.pre_fault.timestamp - timedelta(milliseconds=100)
        fault_time = self.tfr.fault.timestamp
        
        # Find event times
        trip_time = None
        pickup_time = None
        breaker_time = None
        
        for event in self.tfr.events:
            if event.event_type == "trip_command":
                trip_time = event.timestamp
            elif event.event_type == "protection_start":
                pickup_time = event.timestamp
            elif event.event_type == "breaker_open":
                breaker_time = event.timestamp
        
        with open(filepath, 'w') as f:
            for sample_num in range(self.total_samples):
                # Calculate current time
                time_offset = sample_num / self.sample_rate
                current_time = start_time + timedelta(seconds=time_offset)
                time_us = int(time_offset * 1e6)
                
                # Determine phase of fault (pre-fault, during fault, post-fault)
                if current_time < fault_time:
                    # Pre-fault values
                    va = self.tfr.pre_fault.voltage_kv["A"]
                    vb = self.tfr.pre_fault.voltage_kv["B"]
                    vc = self.tfr.pre_fault.voltage_kv["C"]
                    ia = self.tfr.pre_fault.current_a["A"]
                    ib = self.tfr.pre_fault.current_a["B"]
                    ic = self.tfr.pre_fault.current_a["C"]
                    freq = self.tfr.pre_fault.frequency_hz
                    fault_active = 0
                elif current_time < self.tfr.post_fault.timestamp:
                    # During fault - interpolate between fault peak values
                    va = self.tfr.fault.voltage_kv["A"]
                    vb = self.tfr.fault.voltage_kv["B"]
                    vc = self.tfr.fault.voltage_kv["C"]
                    ia = self.tfr.fault.current_a["A"]
                    ib = self.tfr.fault.current_a["B"]
                    ic = self.tfr.fault.current_a["C"]
                    freq = self.tfr.fault.frequency_hz
                    fault_active = 1
                else:
                    # Post-fault values
                    va = self.tfr.post_fault.voltage_kv["A"]
                    vb = self.tfr.post_fault.voltage_kv["B"]
                    vc = self.tfr.post_fault.voltage_kv["C"]
                    ia = self.tfr.post_fault.current_a["A"]
                    ib = self.tfr.post_fault.current_a["B"]
                    ic = self.tfr.post_fault.current_a["C"]
                    freq = self.tfr.post_fault.frequency_hz
                    fault_active = 0
                
                # Digital status bits
                breaker_closed = 1 if (breaker_time is None or current_time < breaker_time) else 0
                trip_cmd = 1 if (trip_time and current_time >= trip_time and current_time < breaker_time) else 0
                pickup = 1 if (pickup_time and current_time >= pickup_time and current_time < self.tfr.post_fault.timestamp) else 0
                prot_armed = 1
                
                # Write data line: sample_num, time_us, analog_values, digital_values
                f.write(f"{sample_num},{time_us},{va:.6f},{vb:.6f},{vc:.6f},{ia:.3f},{ib:.3f},{ic:.3f},{freq:.3f},")
                f.write(f"{breaker_closed},{fault_active},{prot_armed},{trip_cmd},{pickup}\n")
    
    def _write_hdr_file(self, filepath: str):
        """Write COMTRADE header file (.hdr) with metadata"""
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("COMTRADE TRANSIENT FAULT RECORD\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Record ID: {self.tfr.id}\n")
            f.write(f"Fault Type: {self.tfr.fault_type}\n")
            f.write(f"Affected Phases: {', '.join(self.tfr.affected_phases)}\n")
            f.write(f"Fault Duration: {self.tfr.duration_ms} ms\n")
            f.write(f"Created: {self.tfr.created_at.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
            f.write(f"Status: {self.tfr.status}\n\n")
            
            f.write("PRE-FAULT CONDITIONS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Timestamp: {self.tfr.pre_fault.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
            f.write(f"  Voltage (kV): A={self.tfr.pre_fault.voltage_kv['A']:.2f}, B={self.tfr.pre_fault.voltage_kv['B']:.2f}, C={self.tfr.pre_fault.voltage_kv['C']:.2f}\n")
            f.write(f"  Current (A):  A={self.tfr.pre_fault.current_a['A']:.1f}, B={self.tfr.pre_fault.current_a['B']:.1f}, C={self.tfr.pre_fault.current_a['C']:.1f}\n")
            f.write(f"  Frequency: {self.tfr.pre_fault.frequency_hz:.2f} Hz\n\n")
            
            f.write("FAULT CONDITIONS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Timestamp: {self.tfr.fault.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
            f.write(f"  Voltage (kV): A={self.tfr.fault.voltage_kv['A']:.2f}, B={self.tfr.fault.voltage_kv['B']:.2f}, C={self.tfr.fault.voltage_kv['C']:.2f}\n")
            f.write(f"  Current (A):  A={self.tfr.fault.current_a['A']:.1f}, B={self.tfr.fault.current_a['B']:.1f}, C={self.tfr.fault.current_a['C']:.1f}\n")
            f.write(f"  Frequency: {self.tfr.fault.frequency_hz:.2f} Hz\n\n")
            
            f.write("POST-FAULT CONDITIONS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Timestamp: {self.tfr.post_fault.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
            f.write(f"  Voltage (kV): A={self.tfr.post_fault.voltage_kv['A']:.2f}, B={self.tfr.post_fault.voltage_kv['B']:.2f}, C={self.tfr.post_fault.voltage_kv['C']:.2f}\n")
            f.write(f"  Current (A):  A={self.tfr.post_fault.current_a['A']:.1f}, B={self.tfr.post_fault.current_a['B']:.1f}, C={self.tfr.post_fault.current_a['C']:.1f}\n")
            f.write(f"  Frequency: {self.tfr.post_fault.frequency_hz:.2f} Hz\n\n")
            
            f.write("EVENT SEQUENCE:\n")
            f.write("-" * 40 + "\n")
            for i, event in enumerate(self.tfr.events, 1):
                f.write(f"  {i}. {event.timestamp.strftime('%H:%M:%S.%f')[:-3]} - {event.event_type}: {event.description}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("CHANNEL INFORMATION:\n")
            f.write("=" * 80 + "\n")
            f.write("Analog Channels (7):\n")
            f.write("  1. Va  - Phase A Voltage (kV)\n")
            f.write("  2. Vb  - Phase B Voltage (kV)\n")
            f.write("  3. Vc  - Phase C Voltage (kV)\n")
            f.write("  4. Ia  - Phase A Current (A)\n")
            f.write("  5. Ib  - Phase B Current (A)\n")
            f.write("  6. Ic  - Phase C Current (A)\n")
            f.write("  7. Freq - System Frequency (Hz)\n\n")
            
            f.write("Digital Channels (5):\n")
            f.write("  1. BKR_52     - Circuit Breaker Status (1=closed, 0=open)\n")
            f.write("  2. FAULT_ACT  - Fault Active Flag (1=active, 0=cleared)\n")
            f.write("  3. PROT_ARM   - Protection Armed (1=armed)\n")
            f.write("  4. TRIP_CMD   - Trip Command Issued (1=active)\n")
            f.write("  5. PICKUP     - Protection Pickup (1=active)\n\n")
            
            f.write(f"Sampling Rate: {self.sample_rate} Hz ({self.samples_per_cycle} samples/cycle)\n")
            f.write(f"Total Samples: {self.total_samples}\n")
            f.write(f"Record Duration: {self.duration_seconds:.3f} seconds\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("Generated by: Python RTU IEC 104 Simulator\n")
            f.write(f"Export Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write("=" * 80 + "\n")


def export_tfr_to_comtrade(tfr: TFRDetail, output_dir: str = "./comtrade_exports", 
                           sample_rate: int = 4000) -> Dict[str, str]:
    """
    Export a TFR to COMTRADE format.
    
    Args:
        tfr: Transient fault record to export
        output_dir: Directory for output files
        sample_rate: Sampling rate in Hz (default 4000 Hz = 80 samples/cycle @ 50Hz)
    
    Returns:
        Dictionary with paths to generated files
    """
    # Create filename based on TFR metadata
    timestamp = tfr.created_at.strftime("%Y%m%d_%H%M%S")
    base_filename = f"TFR_{tfr.id:04d}_{tfr.fault_type}_{timestamp}"
    
    exporter = ComtradeExporter(tfr, sample_rate)
    return exporter.export(output_dir, base_filename)
