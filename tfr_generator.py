"""
Synthetic transient fault record generator with realistic electrical values.
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from config import (
    FaultType, 
    FAULT_TEMPLATES,
    VOLTAGE_VARIATION_PERCENT,
    CURRENT_VARIATION_PERCENT,
    TIMING_VARIATION_MS,
    FREQUENCY_VARIATION_HZ
)
from models import MeasurementData, ProtectionEvent


class TFRGenerator:
    """Generates synthetic transient fault records from predefined templates"""
    
    def __init__(self):
        self.templates = FAULT_TEMPLATES
    
    def generate(self, fault_type: FaultType, base_time: datetime = None) -> Dict[str, Any]:
        """
        Generate a complete transient fault record.
        
        Args:
            fault_type: Type of fault to generate
            base_time: Base timestamp for the fault sequence (defaults to now)
        
        Returns:
            Dictionary containing complete TFR data with measurements and events
        """
        if fault_type not in self.templates:
            raise ValueError(f"Unknown fault type: {fault_type}")
        
        template = self.templates[fault_type]
        if base_time is None:
            base_time = datetime.utcnow()
        
        # Apply randomization to duration
        duration_ms = random.randint(*template["duration_ms_range"])
        
        # Calculate event timestamps
        fault_inception_time = base_time
        pickup_time = fault_inception_time + timedelta(
            milliseconds=template["pickup_time_ms"] + random.randint(-TIMING_VARIATION_MS, TIMING_VARIATION_MS)
        )
        trip_time = fault_inception_time + timedelta(
            milliseconds=template["trip_time_ms"] + random.randint(-TIMING_VARIATION_MS, TIMING_VARIATION_MS)
        )
        breaker_open_time = fault_inception_time + timedelta(
            milliseconds=template["breaker_time_ms"] + random.randint(-TIMING_VARIATION_MS, TIMING_VARIATION_MS)
        )
        fault_clear_time = fault_inception_time + timedelta(milliseconds=duration_ms)
        
        # Generate pre-fault measurements (5 seconds before fault)
        pre_fault_time = fault_inception_time - timedelta(seconds=5)
        pre_fault = self._generate_measurement(
            pre_fault_time,
            template["pre_fault"],
            add_variation=True
        )
        
        # Generate fault measurements (at peak fault conditions)
        fault_peak_time = fault_inception_time + timedelta(milliseconds=10)
        fault = self._generate_measurement(
            fault_peak_time,
            template["fault"],
            add_variation=True
        )
        
        # Generate post-fault measurements (5 seconds after clearing)
        post_fault_time = fault_clear_time + timedelta(seconds=5)
        post_fault = self._generate_measurement(
            post_fault_time,
            template["pre_fault"],  # Return to pre-fault values
            add_variation=True
        )
        
        # Generate protection events
        events = [
            ProtectionEvent(
                timestamp=fault_inception_time,
                event_type="fault_inception",
                description=f"{template['description']} detected"
            ),
            ProtectionEvent(
                timestamp=pickup_time,
                event_type="protection_start",
                description="Protection relay pickup"
            ),
            ProtectionEvent(
                timestamp=trip_time,
                event_type="trip_command",
                description="Trip command issued"
            ),
            ProtectionEvent(
                timestamp=breaker_open_time,
                event_type="breaker_open",
                description="Circuit breaker opened"
            ),
            ProtectionEvent(
                timestamp=fault_clear_time,
                event_type="fault_cleared",
                description="Fault cleared"
            ),
        ]
        
        # Package complete TFR data
        tfr_data = {
            "fault_type": fault_type.value,
            "duration_ms": duration_ms,
            "affected_phases": template["affected_phases"],
            "pre_fault": pre_fault.model_dump(),
            "fault": fault.model_dump(),
            "post_fault": post_fault.model_dump(),
            "events": [evt.model_dump() for evt in events],
            "created_at": base_time,
        }
        
        return tfr_data
    
    def _generate_measurement(
        self, 
        timestamp: datetime, 
        values: Dict[str, Any],
        add_variation: bool = True
    ) -> MeasurementData:
        """
        Generate a measurement data point with optional randomization.
        
        Args:
            timestamp: Measurement timestamp
            values: Template values (voltage_kv, current_a, frequency_hz)
            add_variation: Whether to add realistic random variation
        
        Returns:
            MeasurementData instance
        """
        voltage_kv = values["voltage_kv"].copy()
        current_a = values["current_a"].copy()
        frequency_hz = values["frequency_hz"]
        
        if add_variation:
            # Add voltage variation
            for phase in voltage_kv:
                variation = random.uniform(
                    -VOLTAGE_VARIATION_PERCENT / 100,
                    VOLTAGE_VARIATION_PERCENT / 100
                )
                voltage_kv[phase] *= (1 + variation)
            
            # Add current variation
            for phase in current_a:
                variation = random.uniform(
                    -CURRENT_VARIATION_PERCENT / 100,
                    CURRENT_VARIATION_PERCENT / 100
                )
                current_a[phase] *= (1 + variation)
            
            # Add frequency variation
            frequency_hz += random.uniform(-FREQUENCY_VARIATION_HZ, FREQUENCY_VARIATION_HZ)
        
        # Round values for realistic precision
        voltage_kv = {k: round(v, 2) for k, v in voltage_kv.items()}
        current_a = {k: round(v, 1) for k, v in current_a.items()}
        frequency_hz = round(frequency_hz, 2)
        
        return MeasurementData(
            timestamp=timestamp,
            voltage_kv=voltage_kv,
            current_a=current_a,
            frequency_hz=frequency_hz
        )


def get_fault_type_info() -> List[Dict[str, Any]]:
    """Get information about all available fault types"""
    info_list = []
    for fault_type, template in FAULT_TEMPLATES.items():
        duration_range = template["duration_ms_range"]
        info_list.append({
            "name": fault_type.value,
            "description": template["description"],
            "affected_phases": template["affected_phases"],
            "typical_duration_ms": f"{duration_range[0]}-{duration_range[1]}"
        })
    return info_list


# Global generator instance
generator = TFRGenerator()
