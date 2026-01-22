"""
IEC 60870-5-104 server implementation for RTU.
Handles General Interrogation, spontaneous transmission, and clock synchronization.
"""
import threading
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import c104

from config import RTU_ADDRESS, IEC104_PORT, IOARange
from models import TFRDetail

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IEC104Server:
    """IEC 104 RTU server with TFR data transmission"""
    
    def __init__(self, port: int = IEC104_PORT, common_address: int = RTU_ADDRESS):
        self.port = port
        self.common_address = common_address
        self.server: Optional[c104.Server] = None
        self.station: Optional[c104.Station] = None
        self.running = False
        self.lock = threading.Lock()
        
        # Current data point values (for GI responses)
        self.current_data: Dict[int, Any] = {}
        self.connected_clients = 0
        
        # COMTRADE availability tracking
        self.comtrade_available_tfrs = set()  # Set of TFR IDs with COMTRADE available
        self.latest_comtrade_tfr_id = 0
        
        # Initialize default values
        self._init_default_values()
    
    def _init_default_values(self):
        """Initialize all data points with default values"""
        with self.lock:
            # Pre-fault measurements (normal operation)
            self.current_data[IOARange.PRE_FAULT_VA] = 231.0
            self.current_data[IOARange.PRE_FAULT_VB] = 231.0
            self.current_data[IOARange.PRE_FAULT_VC] = 231.0
            self.current_data[IOARange.PRE_FAULT_IA] = 1600.0
            self.current_data[IOARange.PRE_FAULT_IB] = 1600.0
            self.current_data[IOARange.PRE_FAULT_IC] = 1600.0
            self.current_data[IOARange.PRE_FAULT_FREQ] = 50.0
            
            # Fault measurements (cleared state)
            self.current_data[IOARange.FAULT_VA] = 231.0
            self.current_data[IOARange.FAULT_VB] = 231.0
            self.current_data[IOARange.FAULT_VC] = 231.0
            self.current_data[IOARange.FAULT_IA] = 1600.0
            self.current_data[IOARange.FAULT_IB] = 1600.0
            self.current_data[IOARange.FAULT_IC] = 1600.0
            self.current_data[IOARange.FAULT_FREQ] = 50.0
            
            # Status points
            self.current_data[IOARange.BREAKER_POSITION] = 2  # ON (2)
            self.current_data[IOARange.FAULT_ACTIVE] = False
            self.current_data[IOARange.PROTECTION_ARMED] = True
            
            # COMTRADE recording signals (normal/idle state)
            self.current_data[IOARange.COMTRADE_RECORDING_ACTIVE] = False  # Not recording
            self.current_data[IOARange.COMTRADE_RECORDER_READY] = True     # Ready to record
            self.current_data[IOARange.COMTRADE_FILE_READY] = False        # No file available
            self.current_data[IOARange.COMTRADE_LATEST_TFR_ID] = 0
            
            # Device clock
            self.current_data[IOARange.DEVICE_CLOCK] = datetime.now()
    
    def start(self):
        """Start the IEC 104 server"""
        logger.info(f"Starting IEC 104 server on port {self.port}")
        
        try:
            # Create server instance
            self.server = c104.Server(ip="0.0.0.0", port=self.port)
            self.station = self.server.add_station(common_address=self.common_address)
            
            # Add data points for all IOAs
            self._add_data_points()
            
            # Set up event handlers - only use available methods
            self.server.on_connect(self._on_client_connect)
            
            # Start server
            self.server.start()
            self.running = True
            logger.info(f"IEC 104 server started on port {self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start IEC 104 server: {e}")
            raise
    
    def _add_data_points(self):
        """Add all data points to the station"""
        if not self.station:
            return
        
        # Pre-fault measurements (M_ME_TF_1 - Short floating point with time)
        for ioa in range(IOARange.PRE_FAULT_VA, IOARange.PRE_FAULT_FREQ + 1):
            self.station.add_point(
                io_address=ioa,
                type=c104.Type.M_ME_TF_1,  # Measured value, short floating point with time
                report_ms=0  # No cyclic reporting
            )
        
        # Fault measurements (M_ME_TF_1)
        for ioa in range(IOARange.FAULT_VA, IOARange.FAULT_FREQ + 1):
            self.station.add_point(
                io_address=ioa,
                type=c104.Type.M_ME_TF_1,
                report_ms=0
            )
        
        # Status points
        self.station.add_point(
            io_address=IOARange.BREAKER_POSITION,
            type=c104.Type.M_DP_TB_1,  # Double point with time
            report_ms=0
        )
        self.station.add_point(
            io_address=IOARange.FAULT_ACTIVE,
            type=c104.Type.M_SP_TB_1,  # Single point with time
            report_ms=0
        )
        self.station.add_point(
            io_address=IOARange.PROTECTION_ARMED,
            type=c104.Type.M_SP_TB_1,
            report_ms=0
        )
        
        # Device clock - using M_ME_TD_1 (measured value, normalized with time)
        # Note: Clock sync commands (C_CS_NA_1) are handled separately by the library
        # Clock updates disabled to avoid c104 library compatibility issues
        self.station.add_point(
            io_address=IOARange.DEVICE_CLOCK,
            type=c104.Type.M_ME_TD_1,
            report_ms=0  # No automatic reporting
        )
        
        # COMTRADE recording status signals
        self.station.add_point(
            io_address=IOARange.COMTRADE_RECORDING_ACTIVE,
            type=c104.Type.M_SP_TB_1,  # Single point with time
            report_ms=0  # Spontaneous only
        )
        self.station.add_point(
            io_address=IOARange.COMTRADE_RECORDER_READY,
            type=c104.Type.M_SP_TB_1,  # Single point with time
            report_ms=0  # Spontaneous only
        )
        self.station.add_point(
            io_address=IOARange.COMTRADE_FILE_READY,
            type=c104.Type.M_SP_TB_1,  # Single point with time
            report_ms=0  # Spontaneous only
        )
        self.station.add_point(
            io_address=IOARange.COMTRADE_LATEST_TFR_ID,
            type=c104.Type.M_ME_NC_1,  # Short floating point (TFR ID)
            report_ms=0  # Spontaneous only
        )
        
        # Protection events (M_EP_TE_1 - Event of protection equipment with time)
        for ioa in range(IOARange.PROTECTION_START, IOARange.BREAKER_OPEN_EVENT + 1):
            self.station.add_point(
                io_address=ioa,
                type=c104.Type.M_EP_TE_1,
                report_ms=0
            )
    
    def _on_client_connect(self, server: c104.Server, ip: str) -> bool:
        """Handle client connection"""
        self.connected_clients += 1
        logger.info(f"Client connected from {ip}. Total clients: {self.connected_clients}")
        return True  # Accept connection
    
    def _on_receive_raw(self, data: bytes) -> c104.ResponseState:
        """Handle raw incoming messages - not used in current c104 version"""
        logger.debug(f"Received raw data: {data.hex()}")
        return c104.ResponseState.SUCCESS
    
    def _on_clock_sync(self, ip: str, date_time: datetime) -> c104.ResponseState:
        """
        Handle clock synchronization command from master.
        Accept time from master and update device clock.
        """
        logger.info(f"Clock sync received from {ip}: {date_time}")
        
        # Update internal clock representation
        with self.lock:
            self.current_data[IOARange.DEVICE_CLOCK] = date_time
        
        # Update the data point
        if self.station:
            point = self.station.get_point(IOARange.DEVICE_CLOCK)
            if point:
                # For M_ME_TD_1, we need to send a normalized value
                # We'll use a simple encoding: send 1.0 to indicate clock was set
                point.value = 1.0
                point.report(cause=c104.Cot.ACTIVATION_CON)
        
        logger.info(f"Device clock synchronized to: {date_time}")
        return c104.ResponseState.SUCCESS
    
    def _update_device_clock(self):
        """
        Periodically update the device clock data point with current time.
        Note: Currently disabled due to c104 library compatibility issues.
        Clock synchronization via C_CS_NA_1 commands is still supported.
        """
        # Disabled to avoid c104 library errors with M_ME_TD_1 value assignment
        pass
    
    def update_tfr_data(self, tfr: TFRDetail):
        """
        Update current data points with new TFR and transmit spontaneously.
        
        Args:
            tfr: Complete transient fault record
        """
        if not self.station or not self.running:
            logger.warning("Server not running, cannot update TFR data")
            return
        
        with self.lock:
            # Update pre-fault measurements
            self.current_data[IOARange.PRE_FAULT_VA] = tfr.pre_fault.voltage_kv["A"]
            self.current_data[IOARange.PRE_FAULT_VB] = tfr.pre_fault.voltage_kv["B"]
            self.current_data[IOARange.PRE_FAULT_VC] = tfr.pre_fault.voltage_kv["C"]
            self.current_data[IOARange.PRE_FAULT_IA] = tfr.pre_fault.current_a["A"]
            self.current_data[IOARange.PRE_FAULT_IB] = tfr.pre_fault.current_a["B"]
            self.current_data[IOARange.PRE_FAULT_IC] = tfr.pre_fault.current_a["C"]
            self.current_data[IOARange.PRE_FAULT_FREQ] = tfr.pre_fault.frequency_hz
            
            # Update fault measurements
            self.current_data[IOARange.FAULT_VA] = tfr.fault.voltage_kv["A"]
            self.current_data[IOARange.FAULT_VB] = tfr.fault.voltage_kv["B"]
            self.current_data[IOARange.FAULT_VC] = tfr.fault.voltage_kv["C"]
            self.current_data[IOARange.FAULT_IA] = tfr.fault.current_a["A"]
            self.current_data[IOARange.FAULT_IB] = tfr.fault.current_a["B"]
            self.current_data[IOARange.FAULT_IC] = tfr.fault.current_a["C"]
            self.current_data[IOARange.FAULT_FREQ] = tfr.fault.frequency_hz
            
            # Update status - fault is ACTIVE only during recording
            # If recording is not active, this is historical data and fault should be cleared
            is_recording = self.current_data.get(IOARange.COMTRADE_RECORDING_ACTIVE, False)
            self.current_data[IOARange.FAULT_ACTIVE] = is_recording  # Active only during recording
            self.current_data[IOARange.BREAKER_POSITION] = 1  # OFF after trip
        
        # Transmit spontaneously (COT=3) to all connected clients
        self._transmit_spontaneous(tfr)
        
        logger.info(f"Updated IEC 104 data points with TFR {tfr.id}")
    
    def _transmit_spontaneous(self, tfr: TFRDetail):
        """Transmit new TFR data spontaneously (COT=3) to connected clients"""
        if not self.station:
            return
        
        try:
            # Update and transmit pre-fault measurements
            # Note: c104 library automatically transmits changes when point values are updated
            # The library handles COT internally
            
            point = self.station.get_point(IOARange.PRE_FAULT_VA)
            if point:
                point.value = float(tfr.pre_fault.voltage_kv["A"])
            
            point = self.station.get_point(IOARange.PRE_FAULT_VB)
            if point:
                point.value = float(tfr.pre_fault.voltage_kv["B"])
            
            point = self.station.get_point(IOARange.PRE_FAULT_VC)
            if point:
                point.value = float(tfr.pre_fault.voltage_kv["C"])
            
            # Transmit fault measurements
            point = self.station.get_point(IOARange.FAULT_VA)
            if point:
                point.value = float(tfr.fault.voltage_kv["A"])
            
            point = self.station.get_point(IOARange.FAULT_VB)
            if point:
                point.value = float(tfr.fault.voltage_kv["B"])
            
            point = self.station.get_point(IOARange.FAULT_VC)
            if point:
                point.value = float(tfr.fault.voltage_kv["C"])
            
            # Transmit current measurements
            point = self.station.get_point(IOARange.FAULT_IA)
            if point:
                point.value = float(tfr.fault.current_a["A"])
            
            point = self.station.get_point(IOARange.FAULT_IB)
            if point:
                point.value = float(tfr.fault.current_a["B"])
            
            point = self.station.get_point(IOARange.FAULT_IC)
            if point:
                point.value = float(tfr.fault.current_a["C"])
            
            # Transmit status updates - fault active status based on recording state
            point = self.station.get_point(IOARange.FAULT_ACTIVE)
            if point:
                is_recording = self.current_data.get(IOARange.COMTRADE_RECORDING_ACTIVE, False)
                point.value = is_recording
            
            logger.info(f"Updated IEC 104 points for TFR {tfr.id} - Fault Active: {self.current_data.get(IOARange.FAULT_ACTIVE, False)}")
            
        except Exception as e:
            logger.error(f"Error updating data points: {e}")
    
    def handle_general_interrogation(self):
        """
        Handle General Interrogation (GI) request.
        Respond with all current data point values.
        """
        if not self.station:
            return
        
        logger.info("Handling General Interrogation")
        
        try:
            # Send all current measurements with COT=INTERROGATED
            for ioa, value in self.current_data.items():
                point = self.station.get_point(ioa)
                if point:
                    # Special handling for device clock
                    if ioa == IOARange.DEVICE_CLOCK and isinstance(value, datetime):
                        seconds_since_midnight = (value.hour * 3600 + 
                                                 value.minute * 60 + 
                                                 value.second)
                        point.value = seconds_since_midnight / 86400.0
                    else:
                        point.value = value
                    point.report(cause=c104.Cot.INTERROGATED)
            
            logger.info("General Interrogation completed")
            
        except Exception as e:
            logger.error(f"Error during General Interrogation: {e}")
    
    def signal_comtrade_recording_start(self, tfr_id: int):
        """
        Signal that COMTRADE recording has started (fault detected).
        Updates IOA 1500 (Recording Active) and 1501 (Recorder Ready).
        
        Expected state transition:
        - IOA 1500: 0 → 1 (Recording now active)
        - IOA 1501: 1 → 0 (Recorder now busy)
        - IOA 1502: remains 0 (File not ready yet)
        
        Args:
            tfr_id: The TFR ID being recorded
        """
        if not self.station or not self.running:
            logger.warning("Server not running, cannot signal COMTRADE recording start")
            return
        
        with self.lock:
            # Update internal state - recording started
            self.current_data[IOARange.COMTRADE_RECORDING_ACTIVE] = True
            self.current_data[IOARange.COMTRADE_RECORDER_READY] = False
            # File ready stays false, TFR ID not updated yet
        
        try:
            # Signal recording started (spontaneous)
            point = self.station.get_point(IOARange.COMTRADE_RECORDING_ACTIVE)
            if point:
                point.value = True
                point.transmit(cause=c104.Cot.SPONTANEOUS)
            
            # Signal recorder now busy
            point = self.station.get_point(IOARange.COMTRADE_RECORDER_READY)
            if point:
                point.value = False
                point.transmit(cause=c104.Cot.SPONTANEOUS)
            
            logger.info(f"Signaled COMTRADE recording START for TFR {tfr_id} (IOA 1500=1, 1501=0)")
            
        except Exception as e:
            logger.error(f"Error signaling COMTRADE recording start: {e}")
    
    def signal_comtrade_recording_complete(self, tfr_id: int):
        """
        Signal that COMTRADE recording is complete and file is ready.
        Updates all three IOAs to indicate file available for transfer.
        
        Expected state transition:
        - IOA 1500: 1 → 0 (Recording finished)
        - IOA 1501: 0 → 1 (Recorder ready for next)
        - IOA 1502: 0 → 1 (File ready for transfer)
        - IOA 1503: Updated with TFR ID
        
        Args:
            tfr_id: The TFR ID for which COMTRADE is ready
        """
        if not self.station or not self.running:
            logger.warning("Server not running, cannot signal COMTRADE recording complete")
            return
        
        with self.lock:
            # Track this TFR as having COMTRADE available
            self.comtrade_available_tfrs.add(tfr_id)
            self.latest_comtrade_tfr_id = tfr_id
            
            # Update internal state - recording complete, file ready
            self.current_data[IOARange.COMTRADE_RECORDING_ACTIVE] = False
            self.current_data[IOARange.COMTRADE_RECORDER_READY] = True
            self.current_data[IOARange.COMTRADE_FILE_READY] = True
            self.current_data[IOARange.COMTRADE_LATEST_TFR_ID] = float(tfr_id)
            
            # Clear fault active status when recording completes
            self.current_data[IOARange.FAULT_ACTIVE] = False
        
        try:
            # Signal recording finished (spontaneous)
            point = self.station.get_point(IOARange.COMTRADE_RECORDING_ACTIVE)
            if point:
                point.value = False
                point.transmit(cause=c104.Cot.SPONTANEOUS)
            
            # Signal recorder ready again
            point = self.station.get_point(IOARange.COMTRADE_RECORDER_READY)
            if point:
                point.value = True
                point.transmit(cause=c104.Cot.SPONTANEOUS)
            
            # Signal file ready for transfer
            point = self.station.get_point(IOARange.COMTRADE_FILE_READY)
            if point:
                point.value = True
                point.transmit(cause=c104.Cot.SPONTANEOUS)
            
            # Send TFR ID
            point = self.station.get_point(IOARange.COMTRADE_LATEST_TFR_ID)
            if point:
                point.value = float(tfr_id)
                point.transmit(cause=c104.Cot.SPONTANEOUS)
            
            # Signal fault cleared (spontaneous)
            point = self.station.get_point(IOARange.FAULT_ACTIVE)
            if point:
                point.value = False
                point.transmit(cause=c104.Cot.SPONTANEOUS)
            
            logger.info(f"Signaled COMTRADE recording COMPLETE for TFR {tfr_id} - FAULT CLEARED")
            
        except Exception as e:
            logger.error(f"Error signaling COMTRADE recording complete: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status"""
        # Get actual connected client count from server if available
        if self.server:
            try:
                # Try to get connection count from server
                self.connected_clients = len(self.server.connections) if hasattr(self.server, 'connections') else self.connected_clients
            except:
                pass
        
        return {
            "running": self.running,
            "port": self.port,
            "common_address": self.common_address,
            "connected_clients": self.connected_clients,
            "device_time": self.current_data.get(IOARange.DEVICE_CLOCK, datetime.now()).isoformat(),
            "comtrade_recording_active": self.current_data.get(IOARange.COMTRADE_RECORDING_ACTIVE, False),
            "comtrade_recorder_ready": self.current_data.get(IOARange.COMTRADE_RECORDER_READY, True),
            "comtrade_file_ready": self.current_data.get(IOARange.COMTRADE_FILE_READY, False),
            "comtrade_latest_tfr_id": self.latest_comtrade_tfr_id,
            "comtrade_available_count": len(self.comtrade_available_tfrs),
        }
    
    def stop(self):
        """Stop the IEC 104 server"""
        if self.server and self.running:
            logger.info("Stopping IEC 104 server")
            self.server.stop()
            self.running = False
            logger.info("IEC 104 server stopped")


# Global server instance
iec104_server = IEC104Server()
