import subprocess
import os
import time
import logging
import sqlite3
from PIL import Image, ExifTags, ImageFilter
import PIL
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
from collections import defaultdict
import sys
import gc
from pathlib import Path
import signal

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def handle_termination(signum, frame):
    """Handle termination signals to clean up resources."""
    logging.info("Termination signal received. Cleaning up...")
    observer.stop()
    observer.join()
    sys.exit(0)

# Registering the termination signals
signal.signal(signal.SIGTERM, handle_termination)
signal.signal(signal.SIGINT, handle_termination)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Paths to main directories
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
base_dir.mkdir(parents=True, exist_ok=True)

chemin_images = base_dir / 'screenshots'
chemin_transcriptions = base_dir / 'transcription'
chemin_images.mkdir(parents=True, exist_ok=True)
chemin_transcriptions.mkdir(parents=True, exist_ok=True)

# Path to the JSON file for storing data
json_output_path = base_dir / 'new_texts.json'
logging.info(f"JSON output path: {json_output_path}")

# Dictionary to cache already processed files
processed_files = {}

def wait_for_file_to_finish(file_path):
    """Wait for the file size to stabilize indicating it has finished writing."""
    size = -1
    while size != os.path.getsize(file_path):
        size = os.path.getsize(file_path)
        time.sleep(0.5)
    logging.debug(f"File size stabilized for: {file_path}")

def extract_date_from_image(image_path):
    """Extract date and time from image metadata."""
    try:
        image = Image.open(image_path)
        exif = image._getexif()
        if exif:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                if decoded == "DateTime":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        logging.error(f"Error extracting date from image {str(image_path)}: {e}")
    return None

def preprocess_image(image_path):
    """Preprocess the image to improve quality."""
    try:
        with Image.open(image_path) as img:
            img = img.resize((img.width * 2, img.height * 2), PIL.Image.LANCZOS)
            img = img.filter(ImageFilter.SHARPEN)
            img = img.convert('RGB')  # Convert to RGB mode if needed
            return img
    except Exception as e:
        logging.error(f"Error preprocessing image {str(image_path)}: {e}")
    return None

def save_to_db_and_json(image_data, json_output_path):
    """Save data to SQLite database and JSON file."""
    try:
        db_path = base_dir / 'regular_data.db'
        logging.info(f"Database path: {db_path}")
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        cursor = conn.cursor()

        # Ensure 'images' table exists, create if not
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY,
            image BLOB,
            metadata TEXT,
            date TEXT,
            time TEXT,
            processed INTEGER DEFAULT 0
        )
        ''')

        # Insert into SQLite database
        cursor.execute("INSERT INTO images (image, metadata, date, time, processed) VALUES (?, ?, ?, ?, 0)", 
                       (image_data['image'], image_data['text'], image_data['date'], image_data['time']))
        conn.commit()

        logging.debug(f"Data saved to database: {image_data}")

        # Load existing data
        if os.path.exists(json_output_path) and os.path.getsize(json_output_path) > 0:
            with open(json_output_path, 'r') as json_file:
                transcriptions = json.load(json_file)
        else:
            transcriptions = []

        # Group data by date
        grouped_transcriptions = defaultdict(list)
        for entry in transcriptions:
            grouped_transcriptions[entry['date']].append({"time": entry['time'], "text": entry['text']})
        
        # Add new transcription
        grouped_transcriptions[image_data['date']].append({"time": image_data['time'], "text": image_data['text']})

        # Prepare data for saving
        consolidated_transcriptions = [{"date": date, "entries": entries} for date, entries in grouped_transcriptions.items()]

        # Save updated data
        with open(json_output_path, 'w') as json_file:
            json.dump(consolidated_transcriptions, json_file, indent=4)

        logging.debug(f"Data saved to JSON file: {image_data}")
        
    except sqlite3.Error as e:
        logging.error(f"Error saving to database: {e}")
    finally:
        conn.close()
        gc.collect()

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        """Handle new file creation events."""
        if event.is_directory:
            observer.schedule(FileHandler(), event.src_path, recursive=False)
        else:
            self.handle_file(event.src_path)

    def handle_file(self, file_path):
        """Process the newly created file."""
        if file_path in processed_files:
            return

        try:
            wait_for_file_to_finish(file_path)

            if str(chemin_images) in file_path:
                logging.info(f"Processing new image file: {file_path}")
                
                # Call the Swift command-line tool
                try:
                    result = subprocess.run(["RemindOCR", file_path], capture_output=True, text=True, check=True)
                    recognized_text = result.stdout.strip()
                    logging.info(f"Recognized text: {recognized_text}")

                    # Save to JSON
                    date_time = extract_date_from_image(file_path)
                    if not date_time:
                        date_time = datetime.now()
                    date_str = date_time.strftime("%d %b %Y")
                    time_str = date_time.strftime("%H:%M")

                    image_data = {
                        "image": None,  # Not inserting the image in the database
                        "date": date_str,
                        "time": time_str,
                        "text": recognized_text
                    }

                    logging.debug(f"Processed data: {image_data}")

                    save_to_db_and_json(image_data, json_output_path)

                    # Mark the file as processed
                    processed_files[file_path] = True
                    gc.collect()  # Collect garbage to free up memory

                except subprocess.CalledProcessError as e:
                    logging.error(f"OCR process failed: {e}")
                except Exception as e:
                    logging.error(f"Error processing file: {e}")

        except Exception as e:
            logging.error(f"Error processing file {str(file_path)}: {e}")

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        """Handle new file creation events."""
        if not event.is_directory:
            MyHandler().handle_file(event.src_path)

# Observer to monitor main directories (detect new date folders)
observer = Observer()
observer.schedule(MyHandler(), str(chemin_images), recursive=True)
observer.schedule(MyHandler(), str(chemin_transcriptions), recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)  # Avoid a busy-wait loop
except KeyboardInterrupt:
    handle_termination(signal.SIGINT, None)