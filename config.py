"""
Configuration constants, IOA ranges, and fault templates for RTU.
"""
from enum import Enum
from typing import Dict, List, Any


# IEC 104 Configuration
RTU_ADDRESS = 1
IEC104_PORT = 2404
WEB_PORT = 8080

# IOA (Information Object Address) Ranges
class IOARange:
    """Fixed IOA addressing scheme for IEC 104 data points"""
    # Protection events (M_EP_TE_1, M_EP_TD_1)
    PROTECTION_START = 1000
    PROTECTION_TRIP = 1001
    FAULT_DETECT = 1002
    BREAKER_OPEN_EVENT = 1003
    
    # Pre-fault measurements (M_ME_TF_1) - Short floating point with time
    PRE_FAULT_VA = 1100
    PRE_FAULT_VB = 1101
    PRE_FAULT_VC = 1102
    PRE_FAULT_IA = 1103
    PRE_FAULT_IB = 1104
    PRE_FAULT_IC = 1105
    PRE_FAULT_FREQ = 1106
    
    # Fault measurements (M_ME_TF_1)
    FAULT_VA = 1200
    FAULT_VB = 1201
    FAULT_VC = 1202
    FAULT_IA = 1203
    FAULT_IB = 1204
    FAULT_IC = 1205
    FAULT_FREQ = 1206
    
    # Status points (M_DP_TB_1, M_SP_TB_1)
    BREAKER_POSITION = 1300  # Double point: 0=intermediate, 1=off, 2=on
    FAULT_ACTIVE = 1301  # Single point: 0=inactive, 1=active
    PROTECTION_ARMED = 1302  # Single point
    
    # Clock synchronization (C_CS_NA_1 for command, M_ME_TD_1 for normalized value with time)
    DEVICE_CLOCK = 1400  # Device date/time
    
    # COMTRADE recording status signals (following standard IEC 104 COMTRADE workflow)
    COMTRADE_RECORDING_ACTIVE = 1500  # Single point: 1=Recording in progress, 0=Idle
    COMTRADE_RECORDER_READY = 1501    # Single point: 1=Ready to record, 0=Busy/Fault
    COMTRADE_FILE_READY = 1502        # Single point: 1=File available for transfer, 0=No file
    COMTRADE_LATEST_TFR_ID = 1503     # Measured value: TFR ID of most recent COMTRADE file


class FaultType(str, Enum):
    """Predefined fault types with realistic electrical characteristics"""
    THREE_PHASE_FAULT = "THREE_PHASE_FAULT"
    SINGLE_PHASE_TO_GROUND_A = "SINGLE_PHASE_TO_GROUND_A"
    SINGLE_PHASE_TO_GROUND_B = "SINGLE_PHASE_TO_GROUND_B"
    SINGLE_PHASE_TO_GROUND_C = "SINGLE_PHASE_TO_GROUND_C"
    LINE_TO_LINE_AB = "LINE_TO_LINE_AB"
    LINE_TO_LINE_BC = "LINE_TO_LINE_BC"
    LINE_TO_LINE_CA = "LINE_TO_LINE_CA"
    DOUBLE_LINE_TO_GROUND_AB = "DOUBLE_LINE_TO_GROUND_AB"
    DOUBLE_LINE_TO_GROUND_BC = "DOUBLE_LINE_TO_GROUND_BC"
    DOUBLE_LINE_TO_GROUND_CA = "DOUBLE_LINE_TO_GROUND_CA"


# Fault Templates - Realistic electrical values for each fault type
FAULT_TEMPLATES: Dict[FaultType, Dict[str, Any]] = {
    FaultType.THREE_PHASE_FAULT: {
        "description": "Balanced three-phase fault - all phases affected equally",
        "affected_phases": ["A", "B", "C"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 23.1, "B": 23.1, "C": 23.1},  # ~10% remaining
            "current_a": {"A": 12800, "B": 12800, "C": 12800},  # 8× nominal
            "frequency_hz": 49.8,  # Slight drop during fault
        },
        "duration_ms_range": (80, 150),
        "pickup_time_ms": 15,  # Protection pickup delay
        "trip_time_ms": 25,  # Total trip time from fault
        "breaker_time_ms": 40,  # Breaker operation time
    },
    FaultType.SINGLE_PHASE_TO_GROUND_A: {
        "description": "Single phase A to ground fault",
        "affected_phases": ["A"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 46.2, "B": 231.0, "C": 231.0},  # Phase A drops to ~20%
            "current_a": {"A": 7200, "B": 1600, "C": 1600},  # Phase A current surge
            "frequency_hz": 49.9,
        },
        "duration_ms_range": (100, 200),
        "pickup_time_ms": 20,
        "trip_time_ms": 35,
        "breaker_time_ms": 50,
    },
    FaultType.SINGLE_PHASE_TO_GROUND_B: {
        "description": "Single phase B to ground fault",
        "affected_phases": ["B"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 231.0, "B": 46.2, "C": 231.0},
            "current_a": {"A": 1600, "B": 7200, "C": 1600},
            "frequency_hz": 49.9,
        },
        "duration_ms_range": (100, 200),
        "pickup_time_ms": 20,
        "trip_time_ms": 35,
        "breaker_time_ms": 50,
    },
    FaultType.SINGLE_PHASE_TO_GROUND_C: {
        "description": "Single phase C to ground fault",
        "affected_phases": ["C"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 46.2},
            "current_a": {"A": 1600, "B": 1600, "C": 7200},
            "frequency_hz": 49.9,
        },
        "duration_ms_range": (100, 200),
        "pickup_time_ms": 20,
        "trip_time_ms": 35,
        "breaker_time_ms": 50,
    },
    FaultType.LINE_TO_LINE_AB: {
        "description": "Phase A to phase B fault",
        "affected_phases": ["A", "B"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 115.5, "B": 115.5, "C": 231.0},  # ~50% on faulted phases
            "current_a": {"A": 9600, "B": 9600, "C": 1600},  # 6× nominal
            "frequency_hz": 49.85,
        },
        "duration_ms_range": (80, 120),
        "pickup_time_ms": 18,
        "trip_time_ms": 30,
        "breaker_time_ms": 45,
    },
    FaultType.LINE_TO_LINE_BC: {
        "description": "Phase B to phase C fault",
        "affected_phases": ["B", "C"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 231.0, "B": 115.5, "C": 115.5},
            "current_a": {"A": 1600, "B": 9600, "C": 9600},
            "frequency_hz": 49.85,
        },
        "duration_ms_range": (80, 120),
        "pickup_time_ms": 18,
        "trip_time_ms": 30,
        "breaker_time_ms": 45,
    },
    FaultType.LINE_TO_LINE_CA: {
        "description": "Phase C to phase A fault",
        "affected_phases": ["C", "A"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 115.5, "B": 231.0, "C": 115.5},
            "current_a": {"A": 9600, "B": 1600, "C": 9600},
            "frequency_hz": 49.85,
        },
        "duration_ms_range": (80, 120),
        "pickup_time_ms": 18,
        "trip_time_ms": 30,
        "breaker_time_ms": 45,
    },
    FaultType.DOUBLE_LINE_TO_GROUND_AB: {
        "description": "Phase A and B to ground fault",
        "affected_phases": ["A", "B"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 34.65, "B": 34.65, "C": 231.0},  # ~15% remaining
            "current_a": {"A": 11200, "B": 11200, "C": 1600},  # 7× nominal
            "frequency_hz": 49.75,
        },
        "duration_ms_range": (90, 160),
        "pickup_time_ms": 16,
        "trip_time_ms": 28,
        "breaker_time_ms": 42,
    },
    FaultType.DOUBLE_LINE_TO_GROUND_BC: {
        "description": "Phase B and C to ground fault",
        "affected_phases": ["B", "C"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 231.0, "B": 34.65, "C": 34.65},
            "current_a": {"A": 1600, "B": 11200, "C": 11200},
            "frequency_hz": 49.75,
        },
        "duration_ms_range": (90, 160),
        "pickup_time_ms": 16,
        "trip_time_ms": 28,
        "breaker_time_ms": 42,
    },
    FaultType.DOUBLE_LINE_TO_GROUND_CA: {
        "description": "Phase C and A to ground fault",
        "affected_phases": ["C", "A"],
        "pre_fault": {
            "voltage_kv": {"A": 231.0, "B": 231.0, "C": 231.0},
            "current_a": {"A": 1600, "B": 1600, "C": 1600},
            "frequency_hz": 50.0,
        },
        "fault": {
            "voltage_kv": {"A": 34.65, "B": 231.0, "C": 34.65},
            "current_a": {"A": 11200, "B": 1600, "C": 11200},
            "frequency_hz": 49.75,
        },
        "duration_ms_range": (90, 160),
        "pickup_time_ms": 16,
        "trip_time_ms": 28,
        "breaker_time_ms": 42,
    },
}

# Database Configuration
DATABASE_URL = "sqlite:///./data/rtu.db"
DATABASE_DIR = "./data"

# Randomization parameters
VOLTAGE_VARIATION_PERCENT = 5.0  # ±5% on voltage values
CURRENT_VARIATION_PERCENT = 10.0  # ±10% on current values
TIMING_VARIATION_MS = 10  # ±10ms on timing values
FREQUENCY_VARIATION_HZ = 0.05  # ±0.05Hz on frequency
