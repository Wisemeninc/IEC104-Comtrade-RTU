"""
FastAPI web interface for RTU management and TFR operations.
"""
import os
import zipfile
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import logging

from config import FaultType, IEC104_PORT, WEB_PORT, DATABASE_URL, IOARange
from models import (
    TFRCreate, TFRResponse, TFRDetail, TFRList, 
    FaultTypeInfo, RTUStatus, HealthCheck
)
from database import db
from tfr_generator import generator, get_fault_type_info
from iec104_server import iec104_server
from comtrade_export import export_tfr_to_comtrade

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RTU IEC 104 Server",
    description="Synthetic Transient Fault Record server with IEC 60870-5-104 protocol",
    version="1.0.0"
)

# Mount static files (create directory if it doesn't exist)
os.makedirs("./static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the dashboard HTML"""
    try:
        with open("./static/dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Dashboard not found</h1><p>Please ensure dashboard.html exists in the static directory.</p>",
            status_code=404
        )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint for Docker"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.get("/api/status", response_model=RTUStatus)
async def get_status():
    """Get RTU operational status with current measurements"""
    latest_tfr = db.get_latest_tfr()
    records, total = db.get_tfrs(skip=0, limit=1)
    
    iec104_status = iec104_server.get_status()
    
    # Get current live measurements from IEC 104 server
    current_measurements = None
    fault_active = False
    
    try:
        with iec104_server.lock:
            current_data = iec104_server.current_data
            
            # Check if fault is active
            fault_active = current_data.get(IOARange.FAULT_ACTIVE, False)
            
            # If fault is active, show fault measurements; otherwise show pre-fault
            if fault_active:
                current_measurements = {
                    "voltage_kv": {
                        "A": current_data.get(IOARange.FAULT_VA, 0.0),
                        "B": current_data.get(IOARange.FAULT_VB, 0.0),
                        "C": current_data.get(IOARange.FAULT_VC, 0.0)
                    },
                    "current_a": {
                        "A": current_data.get(IOARange.FAULT_IA, 0.0),
                        "B": current_data.get(IOARange.FAULT_IB, 0.0),
                        "C": current_data.get(IOARange.FAULT_IC, 0.0)
                    },
                    "frequency_hz": current_data.get(IOARange.FAULT_FREQ, 0.0)
                }
            else:
                current_measurements = {
                    "voltage_kv": {
                        "A": current_data.get(IOARange.PRE_FAULT_VA, 0.0),
                        "B": current_data.get(IOARange.PRE_FAULT_VB, 0.0),
                        "C": current_data.get(IOARange.PRE_FAULT_VC, 0.0)
                    },
                    "current_a": {
                        "A": current_data.get(IOARange.PRE_FAULT_IA, 0.0),
                        "B": current_data.get(IOARange.PRE_FAULT_IB, 0.0),
                        "C": current_data.get(IOARange.PRE_FAULT_IC, 0.0)
                    },
                    "frequency_hz": current_data.get(IOARange.PRE_FAULT_FREQ, 0.0)
                }
            
            fault_active = current_data.get(IOARange.FAULT_ACTIVE, False)
    except Exception as e:
        logger.error(f"Error reading current measurements: {e}")
    
    return RTUStatus(
        iec104_port=IEC104_PORT,
        iec104_connected_clients=iec104_status["connected_clients"],
        web_port=WEB_PORT,
        last_tfr_timestamp=latest_tfr.created_at if latest_tfr else None,
        total_tfrs_generated=total,
        database_path=DATABASE_URL,
        comtrade_recording_active=iec104_status.get("comtrade_recording_active", False),
        comtrade_recorder_ready=iec104_status.get("comtrade_recorder_ready", True),
        comtrade_file_ready=iec104_status.get("comtrade_file_ready", False),
        comtrade_latest_tfr_id=iec104_status.get("comtrade_latest_tfr_id", 0),
        comtrade_available_count=iec104_status.get("comtrade_available_count", 0),
        current_measurements=current_measurements,
        fault_active=fault_active
    )


@app.get("/api/tfr/types", response_model=List[FaultTypeInfo])
async def list_fault_types():
    """List all available fault types with descriptions"""
    fault_types = get_fault_type_info()
    return [FaultTypeInfo(**ft) for ft in fault_types]


@app.post("/api/tfr/create", response_model=TFRResponse, status_code=201)
async def create_tfr(request: TFRCreate, background_tasks: BackgroundTasks):
    """
    Create a new transient fault record.
    The TFR will be generated and transmitted via IEC 104.
    """
    try:
        # Generate TFR data
        logger.info(f"Generating TFR for fault type: {request.fault_type}")
        tfr_data = generator.generate(request.fault_type)
        
        # Save to database
        tfr_id = db.save_tfr(tfr_data)
        logger.info(f"Saved TFR {tfr_id} to database")
        
        # Retrieve full TFR details
        tfr_detail = db.get_tfr(tfr_id)
        
        if not tfr_detail:
            raise HTTPException(status_code=500, detail="Failed to retrieve generated TFR")
        
        # Signal COMTRADE recording start (IOA 1500=1, 1501=0) FIRST - do this synchronously
        # to ensure recording state is set before updating TFR data
        iec104_server.signal_comtrade_recording_start(tfr_id)
        
        # Update IEC 104 server and transmit spontaneously
        background_tasks.add_task(iec104_server.update_tfr_data, tfr_detail)
        
        # Calculate recording duration: fault duration + pre-fault (5s) + post-fault (5s) buffers
        recording_duration = (tfr_detail.duration_ms / 1000.0) + 5.0 + 5.0
        
        # Auto-complete recording after the buffer period
        async def auto_complete_recording():
            await asyncio.sleep(recording_duration)
            
            # Generate COMTRADE file
            try:
                output_dir = "/tmp/comtrade_exports"
                files = export_tfr_to_comtrade(tfr_detail, output_dir, sample_rate=4000)
                
                # Create ZIP archive
                zip_filename = f"{files['base']}.zip"
                zip_path = os.path.join(output_dir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_type, file_path in files.items():
                        if file_type != 'base':
                            zipf.write(file_path, os.path.basename(file_path))
                
                logger.info(f"Generated COMTRADE files for TFR {tfr_id}: {zip_filename}")
            except Exception as e:
                logger.error(f"Failed to generate COMTRADE for TFR {tfr_id}: {e}")
            
            # Wait 1 second before signaling ready
            await asyncio.sleep(1.0)
            
            # Now signal recording complete with file ready
            iec104_server.signal_comtrade_recording_complete(tfr_id)
            logger.info(f"COMTRADE recording complete for TFR {tfr_id} after {recording_duration + 1.0:.1f}s - file ready")
        
        background_tasks.add_task(auto_complete_recording)
        
        return TFRResponse(
            id=tfr_id,
            fault_type=request.fault_type.value,
            status="completed",
            created_at=tfr_data["created_at"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating TFR: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create TFR: {str(e)}")


@app.get("/api/tfr/list", response_model=TFRList)
async def list_tfrs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get paginated list of all TFRs"""
    skip = (page - 1) * page_size
    
    records, total = db.get_tfrs(skip=skip, limit=page_size)
    
    tfr_responses = [
        TFRResponse(
            id=record.id,
            fault_type=record.fault_type,
            status=record.status,
            created_at=record.created_at
        )
        for record in records
    ]
    
    return TFRList(
        total=total,
        page=page,
        page_size=page_size,
        records=tfr_responses
    )


@app.get("/api/tfr/{tfr_id}", response_model=TFRDetail)
async def get_tfr_detail(tfr_id: int):
    """Get complete details of a specific TFR including all measurements"""
    tfr = db.get_tfr(tfr_id)
    
    if not tfr:
        raise HTTPException(status_code=404, detail=f"TFR {tfr_id} not found")
    
    return tfr


@app.delete("/api/tfr/{tfr_id}")
async def delete_tfr(tfr_id: int):
    """Delete a TFR (placeholder - not implemented in database layer)"""
    # This would require adding a delete method to the database layer
    raise HTTPException(status_code=501, detail="Delete operation not implemented")


@app.get("/api/tfr/{tfr_id}/comtrade")
async def export_tfr_comtrade(
    tfr_id: int,
    sample_rate: int = Query(4000, ge=1000, le=16000, description="Sampling rate in Hz")
):
    """
    Export a TFR in COMTRADE format (IEEE C37.111).
    Returns a ZIP file containing .cfg, .dat, and .hdr files.
    
    If the file was pre-generated by the recording workflow, it serves that file.
    Otherwise, it generates it on-demand.
    """
    tfr = db.get_tfr(tfr_id)
    
    if not tfr:
        raise HTTPException(status_code=404, detail=f"TFR {tfr_id} not found")
    
    try:
        # Export to COMTRADE format (or use pre-generated if exists)
        output_dir = "/tmp/comtrade_exports"
        files = export_tfr_to_comtrade(tfr, output_dir, sample_rate)
        
        # Create ZIP archive
        zip_filename = f"{files['base']}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        # Check if ZIP already exists from recording workflow
        if not os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_type, file_path in files.items():
                    if file_type != 'base':
                        zipf.write(file_path, os.path.basename(file_path))
        
        # Note: Do NOT signal recording complete here - that's handled by the
        # auto_complete_recording background task after the pre/post-fault buffers
        
        # Return ZIP file
        return FileResponse(
            path=zip_path,
            media_type='application/zip',
            filename=zip_filename,
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting COMTRADE for TFR {tfr_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export COMTRADE: {str(e)}")


@app.get("/api/tfr/export/comtrade/batch")
async def export_all_tfrs_comtrade(
    sample_rate: int = Query(4000, ge=1000, le=16000, description="Sampling rate in Hz"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum TFRs to export")
):
    """
    Export all TFRs in COMTRADE format as a single ZIP archive.
    """
    try:
        records, total = db.get_tfrs(skip=0, limit=limit)
        
        if not records:
            raise HTTPException(status_code=404, detail="No TFRs found")
        
        output_dir = "/tmp/comtrade_exports"
        os.makedirs(output_dir, exist_ok=True)
        
        # Create batch ZIP
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        batch_zip = os.path.join(output_dir, f"TFR_Batch_{timestamp}.zip")
        
        with zipfile.ZipFile(batch_zip, 'w', zipfile.ZIP_DEFLATED) as batch_zipf:
            for record in records:
                tfr = db.get_tfr(record.id)
                if tfr:
                    # Export individual TFR
                    files = export_tfr_to_comtrade(tfr, output_dir, sample_rate)
                    
                    # Add to batch ZIP
                    for file_type, file_path in files.items():
                        if file_type != 'base':
                            arcname = f"TFR_{tfr.id:04d}/{os.path.basename(file_path)}"
                            batch_zipf.write(file_path, arcname)
        
        return FileResponse(
            path=batch_zip,
            media_type='application/zip',
            filename=os.path.basename(batch_zip),
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(batch_zip)}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting batch COMTRADE: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export batch COMTRADE: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Startup event - log server information"""
    logger.info(f"FastAPI server starting on port {WEB_PORT}")
    logger.info(f"IEC 104 server on port {IEC104_PORT}")
    logger.info("COMTRADE availability signaling enabled via IEC 104")
    
    # Load last few TFRs to show in status
    recent_tfrs = db.get_last_n_tfrs(n=5)
    logger.info(f"Loaded {len(recent_tfrs)} recent TFRs from database")
    
    # If there are recent TFRs, update IEC 104 server with the latest one
    if recent_tfrs:
        latest = recent_tfrs[0]
        logger.info(f"Restoring IEC 104 data points from TFR {latest.id}")
        iec104_server.update_tfr_data(latest)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("FastAPI server shutting down")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
