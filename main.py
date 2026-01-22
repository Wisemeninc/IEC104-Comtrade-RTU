"""
Main application entry point.
Starts IEC 104 server and FastAPI web interface in parallel threads.
"""
import os
import sys
import signal
import threading
import logging
import uvicorn
from typing import Optional

from config import IEC104_PORT, WEB_PORT
from iec104_server import iec104_server
from web_api import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_event.set()


def run_iec104_server():
    """Run IEC 104 server in a separate thread"""
    try:
        logger.info("Starting IEC 104 server thread")
        iec104_server.start()
        
        # Keep thread alive until shutdown
        while not shutdown_event.is_set():
            shutdown_event.wait(timeout=1.0)
        
        logger.info("Stopping IEC 104 server")
        iec104_server.stop()
        
    except Exception as e:
        logger.error(f"IEC 104 server error: {e}")
        shutdown_event.set()


def run_fastapi_server():
    """Run FastAPI server"""
    try:
        logger.info(f"Starting FastAPI server on port {WEB_PORT}")
        
        # Configure uvicorn
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=WEB_PORT,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        
        # Run server
        server.run()
        
    except Exception as e:
        logger.error(f"FastAPI server error: {e}")
        shutdown_event.set()


def main():
    """Main entry point - start both servers"""
    logger.info("=" * 60)
    logger.info("RTU IEC 60870-5-104 Server with Synthetic TFR")
    logger.info("=" * 60)
    logger.info(f"IEC 104 Port: {IEC104_PORT}")
    logger.info(f"Web API Port: {WEB_PORT}")
    logger.info("=" * 60)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start IEC 104 server in separate thread
    iec104_thread = threading.Thread(
        target=run_iec104_server,
        name="IEC104-Server",
        daemon=False
    )
    iec104_thread.start()
    
    # Wait a moment for IEC 104 server to initialize
    import time
    time.sleep(2)
    
    # Start FastAPI server in main thread
    try:
        run_fastapi_server()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        shutdown_event.set()
    
    # Wait for IEC 104 thread to complete
    logger.info("Waiting for IEC 104 server thread to complete...")
    iec104_thread.join(timeout=5.0)
    
    logger.info("=" * 60)
    logger.info("RTU Server shutdown complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
