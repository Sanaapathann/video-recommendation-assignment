import uvicorn
import os
import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_port_in_use(port, host='127.0.0.1'):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def find_available_port(start_port, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

if __name__ == "__main__":
    # Get port from environment or use default
    preferred_port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    
    # Check if preferred port is available, or find another one
    if is_port_in_use(preferred_port, host):
        logger.warning(f"Port {preferred_port} is already in use!")
        
        # Find an available port
        port = find_available_port(preferred_port)
        if port:
            logger.info(f"Using alternative port: {port}")
        else:
            # If no ports are available, fall back to a high random port
            port = 0  # Let OS choose a random port
            logger.warning(f"No available ports found in range {preferred_port}-{preferred_port+10}. Using OS-assigned port.")
    else:
        port = preferred_port
        logger.info(f"Using requested port: {port}")
    
    # Run the FastAPI application with Uvicorn
    try:
        logger.info(f"Starting server on {host}:{port}")
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        
        # If that failed, try one more time with OS-assigned port
        if port != 0:
            logger.info("Trying again with OS-assigned port...")
            uvicorn.run(
                "app.main:app",
                host=host,
                port=0,
                reload=True
            ) 