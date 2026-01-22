"""
SQLite persistence layer for transient fault records.
"""
import os
import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from models import Base, TransientFaultRecordDB, TFRDetail, MeasurementData, ProtectionEvent
from config import DATABASE_URL, DATABASE_DIR


class Database:
    """Database manager for TFR persistence"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        # Ensure data directory exists
        os.makedirs(DATABASE_DIR, exist_ok=True)
        
        self.engine = create_engine(database_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def save_tfr(self, tfr_data: dict) -> int:
        """
        Save a transient fault record to database.
        
        Args:
            tfr_data: Dictionary containing TFR data with keys:
                - fault_type: str
                - duration_ms: int
                - affected_phases: list of str
                - pre_fault: dict
                - fault: dict
                - post_fault: dict
                - events: list of dict
        
        Returns:
            ID of the saved record
        """
        session = self.get_session()
        try:
            # Convert datetime objects to ISO format strings for JSON storage
            def serialize_for_json(obj):
                if isinstance(obj, dict):
                    return {k: serialize_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [serialize_for_json(item) for item in obj]
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                else:
                    return obj
            
            record = TransientFaultRecordDB(
                fault_type=tfr_data["fault_type"],
                duration_ms=tfr_data["duration_ms"],
                affected_phases=",".join(tfr_data["affected_phases"]),
                pre_fault_json=serialize_for_json(tfr_data["pre_fault"]),
                fault_json=serialize_for_json({**tfr_data["fault"], "events": tfr_data["events"]}),
                post_fault_json=serialize_for_json(tfr_data["post_fault"]),
                status="completed"
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_tfr(self, tfr_id: int) -> Optional[TFRDetail]:
        """Get a specific TFR by ID"""
        session = self.get_session()
        try:
            record = session.query(TransientFaultRecordDB).filter(
                TransientFaultRecordDB.id == tfr_id
            ).first()
            
            if not record:
                return None
            
            return self._convert_to_detail(record)
        finally:
            session.close()
    
    def get_tfrs(self, skip: int = 0, limit: int = 20) -> tuple[List[TransientFaultRecordDB], int]:
        """
        Get paginated list of TFRs.
        
        Returns:
            Tuple of (records, total_count)
        """
        session = self.get_session()
        try:
            total = session.query(TransientFaultRecordDB).count()
            records = session.query(TransientFaultRecordDB).order_by(
                desc(TransientFaultRecordDB.created_at)
            ).offset(skip).limit(limit).all()
            return records, total
        finally:
            session.close()
    
    def get_last_n_tfrs(self, n: int = 10) -> List[TFRDetail]:
        """Get the last N TFRs (for startup restoration)"""
        session = self.get_session()
        try:
            records = session.query(TransientFaultRecordDB).order_by(
                desc(TransientFaultRecordDB.created_at)
            ).limit(n).all()
            
            return [self._convert_to_detail(record) for record in records]
        finally:
            session.close()
    
    def get_latest_tfr(self) -> Optional[TransientFaultRecordDB]:
        """Get the most recent TFR"""
        session = self.get_session()
        try:
            return session.query(TransientFaultRecordDB).order_by(
                desc(TransientFaultRecordDB.created_at)
            ).first()
        finally:
            session.close()
    
    def _convert_to_detail(self, record: TransientFaultRecordDB) -> TFRDetail:
        """Convert database record to TFRDetail model"""
        # Deserialize datetime strings back to datetime objects
        def deserialize_from_json(obj):
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    if k == 'timestamp' and isinstance(v, str):
                        result[k] = datetime.fromisoformat(v)
                    else:
                        result[k] = deserialize_from_json(v)
                return result
            elif isinstance(obj, list):
                return [deserialize_from_json(item) for item in obj]
            else:
                return obj
        
        # Reconstruct measurement data
        pre_fault_data = deserialize_from_json(record.pre_fault_json)
        fault_data = deserialize_from_json(record.fault_json)
        post_fault_data = deserialize_from_json(record.post_fault_json)
        
        pre_fault = MeasurementData(**pre_fault_data)
        fault = MeasurementData(**{k: v for k, v in fault_data.items() if k != 'events'})
        post_fault = MeasurementData(**post_fault_data)
        
        # Reconstruct events (stored in fault_json)
        events = []
        if "events" in fault_data:
            events = [ProtectionEvent(**evt) for evt in fault_data["events"]]
        
        return TFRDetail(
            id=record.id,
            created_at=record.created_at,
            fault_type=record.fault_type,
            duration_ms=record.duration_ms,
            affected_phases=record.affected_phases.split(","),
            status=record.status,
            pre_fault=pre_fault,
            fault=fault,
            post_fault=post_fault,
            events=events
        )


# Global database instance
db = Database()
