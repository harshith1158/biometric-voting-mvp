#!/usr/bin/env python
import sys
import logging
sys.path.insert(0, '.')

# Configure logging BEFORE importing the app
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend_debug.log')
    ]
)

from app.main import create_app

print("=== BACKEND RESTARTED CLEAN ===")

if __name__ == '__main__':
    app = create_app()
    # Enable Flask logging
    app.logger.setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=True)
