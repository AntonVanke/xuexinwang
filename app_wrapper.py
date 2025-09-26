#!/usr/bin/env python3
"""
Wrapper script for running the Flask application with command-line arguments
This file is needed for PyInstaller to properly handle command-line arguments
"""

import sys
import json
import os
from app import app, init_db

def main():
    # Initialize database
    init_db()

    # Default configuration
    host = "0.0.0.0"  # 默认允许公网访问
    port = 5000
    debug = False

    # Check for command-line arguments
    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                print(f"Invalid port: {sys.argv[i + 1]}")
                sys.exit(1)
        elif arg == "--debug":
            debug = True

    # Check for config file
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                host = config.get('host', host)
                port = config.get('port', port)
                debug = config.get('debug', debug)
        except Exception as e:
            print(f"Error reading config file: {e}")

    # Run the application
    print(f"Starting XueXinWang Archive Management System...")
    print(f"Listening on {host}:{port}")
    print(f"Access URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")

    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()