"""
This script sets up a Waitress server to serve the Flask application.

The Waitress server is chosen for its simplicity and ability to serve WSGI applications, like Flask, efficiently.

Usage:
1. Ensure that the necessary dependencies, including Waitress and Flask, are installed.
2. Import your Flask application (named 'app' in this script).
3. Define the run_server function to configure and start the Waitress server.
4. Adjust the host, port, and number of threads as needed.
5. Run the script to start the server.

Note: This script assumes that the Flask application is defined in a file named 'app.py' in the same directory.
"""
from waitress import serve # type: ignore
import logging
import os

# Import your Flask application
from app import app

# Create the Waitress server
def run_server():
    host = '127.0.0.1'
    port = 5000
    threads = 4
    print(f"Server was running at http://{host}:{5000} with {threads} threads")
    serve(app, host=host, port=port, threads=threads)

if __name__ == "__main__":
    run_server()
