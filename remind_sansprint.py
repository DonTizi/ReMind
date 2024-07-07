# Author: Elyes Rayane Melbouci
# Purpose: This script sets up and manages the RemindEnchanted application, which includes initializing a SQLite database, handling JSON files, running various scripts, and managing processes through a menu bar application.

#!/usr/bin/env python3
import os
import subprocess
import threading
import time
import json
import sys
from pathlib import Path
import rumps
import signal
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Get the base directory for the project
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
base_dir.mkdir(parents=True, exist_ok=True)

# Path to the regular_db database
regular_db_path = base_dir / 'regular_data.db'

# Paths to JSON files
all_texts_path = base_dir / 'all_texts.json'
new_texts_path = base_dir / 'new_texts.json'

# Script to create the regular_db database if it does not exist
regular_db_script = resource_path('Regular_database.py')

# Scripts to run
scripts = {
    "image_record": resource_path('record_photo.py'),
    "pipeline": resource_path('pipeline_db.py'),
    "ingestion": resource_path('ingestion.py'),
    "adding_vectore": resource_path('adding_vectore.py'),
    "swift": resource_path('swift.py'),
    "deletedb": resource_path('delete_imagedb.py')
}

# Check and create JSON files if they do not exist
if not os.path.exists(all_texts_path):
    sample_data = [
        {
            "date": "22 May 2024",
            "entries": [
                {
                    "time": "14:53",
                    "text": "Sample Data"
                }
            ]
        }
    ]
    with open(all_texts_path, 'w') as f:
        json.dump(sample_data, f, indent=4)
    logging.debug(f"Created sample all_texts.json at {all_texts_path}")

if not os.path.exists(new_texts_path):
    sample_data = [
        {
            "date": "22 May 2024",
            "entries": [
                {
                    "time": "14:53",
                    "text": "Sample Data"
                }
            ]
        }
    ]
    with open(new_texts_path, 'w') as f:
        json.dump(sample_data, f)
    logging.debug(f"Created sample new_texts.json at {new_texts_path}")

# Check for the existence of the regular_db and run the script if it does not exist
if not os.path.exists(regular_db_path):
    logging.debug(f"Database not found at {regular_db_path}, running {regular_db_script}")
    subprocess.call(['python', regular_db_script])

# List to store all launched processes
all_processes = []

# Variable to control the execution of loops
running = True

# Function to run scripts and manage processes
def run_script(script):
    logging.debug(f"Running script {script}")
    process = subprocess.Popen(['python', script])
    all_processes.append(process)
    process.wait()
    logging.debug(f"Completed script {script}")

# Function to run ingestion, adding vectors, and indexing
def pipeline():
    global running
    while running:
        for script in ["ingestion", "adding_vectore", "deletedb"]:
            if not running:
                break
            run_script(scripts[script])
        time.sleep(1200)

# Function to stop all processes
def stop_all_processes():
    global running
    running = False
    logging.debug("Stopping all processes")
    
    # Stop all launched processes
    for process in all_processes:
        try:
            process.terminate()
            process.wait(timeout=5)
            logging.debug(f"Terminated process {process.pid}")
        except Exception as e:
            logging.error(f"Error terminating process {process.pid}: {e}")
            process.kill()
    
    # Get the PID of the current process
    current_process = psutil.Process(os.getpid())
    
    # Get all child processes
    children = current_process.children(recursive=True)
    
    # Terminate all child processes
    for child in children:
        try:
            child.terminate()
            child.wait(timeout=5)
            logging.debug(f"Terminated child process {child.pid}")
        except Exception as e:
            logging.error(f"Error terminating child process {child.pid}: {e}")
            child.kill()
    
    # Terminate the main process
    os.kill(os.getpid(), signal.SIGTERM)

# Class for the menu bar application
class RemindEnchantedApp(rumps.App):
    def __init__(self):
        icon_path = resource_path('remindbg.png')
        super(RemindEnchantedApp, self).__init__("RemindEnchanted", icon=icon_path)
        
    @rumps.clicked("Quit")
    def quit(self, _):
        stop_all_processes()
        rumps.quit_application()

# Main function
def main():
    # Run audio, image recording, and pipeline scripts
    for script in ["swift", "image_record", "pipeline"]:
        threading.Thread(target=run_script, args=(scripts[script],)).start()

    # Start the pipeline in a separate thread
    threading.Thread(target=pipeline).start()

    logging.debug("Loading... server started!")

    # Run the menu bar application
    RemindEnchantedApp().run()

if __name__ == "__main__":
    main()
