"""
Pydantic models and SQLAlchemy ORM for transient fault records.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from config import FaultType

Base = declarative_base()


# SQLAlchemy ORM Model
class TransientFaultRecordDB(Base):
    """Database model for storing transient fault records"""
    __tablename__ = "transient_fault_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    fault_type = Column(String(50), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    affected_phases = Column(String(20), nullable=False)  # Comma-separated: "A,B,C"
    pre_fault_json = Column(JSON, nullable=False)
    fault_json = Column(JSON, nullable=False)
    post_fault_json = Column(JSON, nullable=False)
    status = Column(String(20), default="completed", nullable=False)
    
    def __repr__(self):
        return f"<TFR(id={self.id}, type={self.fault_type}, duration={self.duration_ms}ms)>"


# Pydantic Models for API
class MeasurementData(BaseModel):
    """Single point-in-time electrical measurements"""
    timestamp: datetime
    voltage_kv: Dict[str, float] = Field(description="Phase voltages in kV (A, B, C)")
    current_a: Dict[str, float] = Field(description="Phase currents in Amperes (A, B, C)")
    frequency_hz: float = Field(description="System frequency in Hz")


class ProtectionEvent(BaseModel):
    """Protection system event"""
    timestamp: datetime
    event_type: str = Field(description="Event type: start, trip, breaker_open")
    description: str


class TFRCreate(BaseModel):
    """Request to create a new transient fault record"""
    fault_type: FaultType = Field(description="Type of fault to generate")


class TFRResponse(BaseModel):
    """Response after creating a TFR"""
    id: int
    fault_type: str
    status: str
    created_at: datetime


class TFRDetail(BaseModel):
    """Complete transient fault record with all measurements"""
    id: int
    created_at: datetime
    fault_type: str
    duration_ms: int
    affected_phases: List[str]
    status: str
    pre_fault: MeasurementData
    fault: MeasurementData
    post_fault: MeasurementData
    events: List[ProtectionEvent]
    
    class Config:
        from_attributes = True


class TFRList(BaseModel):
    """Paginated list of TFRs"""
    total: int
    page: int
    page_size: int
    records: List[TFRResponse]


class FaultTypeInfo(BaseModel):
    """Information about a fault type"""
    name: str
    description: str
    affected_phases: List[str]
    typical_duration_ms: str


class RTUStatus(BaseModel):
    """RTU operational status"""
    iec104_port: int
    iec104_connected_clients: int
    web_port: int
    last_tfr_timestamp: Optional[datetime]
    total_tfrs_generated: int
    database_path: str
    comtrade_recording_active: bool = False
    comtrade_recorder_ready: bool = True
    comtrade_file_ready: bool = False
    comtrade_latest_tfr_id: int = 0
    comtrade_available_count: int = 0
    current_measurements: Optional[Dict[str, Any]] = None
    fault_active: bool = False


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
