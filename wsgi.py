from app import app, cleanup, kill_existing_process
import signal
import sys
import logging

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    logger.info('Shutting down gracefully...')
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    try:
        # Kill any existing process on port 5000
        kill_existing_process(5000)
        # Register cleanup on exit
        import atexit
        atexit.register(cleanup)
        app.run()
    except Exception as e:
        logger.error(f"Error: {e}")
        cleanup() 