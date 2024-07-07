# Author: Elyes Rayane Melbouci
# Purpose: This script sets up a SQLite database with tables for storing images and transcriptions, including creating necessary indexes to optimize search queries.

import sqlite3
import os
import sys
from pathlib import Path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Define the database path
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
base_dir.mkdir(parents=True, exist_ok=True)
db_path = base_dir / 'regular_data.db'

# Connect to the database
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Create the table for images with columns for date, time, and image_path
cursor.execute('''
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY,
    image_path TEXT,
    image BLOB,
    metadata TEXT,
    date TEXT,
    time TEXT,
    processed INTEGER DEFAULT 0
)
''')

# Create the table for transcriptions with columns for date and time
cursor.execute('''
CREATE TABLE IF NOT EXISTS transcriptions (
    id INTEGER PRIMARY KEY,
    title TEXT,
    transcription TEXT,
    date TEXT,
    time TEXT,
    additional_metadata TEXT
)
''')

# Add indexes to optimize searches
cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_metadata ON images (metadata)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_date ON images (date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_time ON images (time)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_transcription ON transcriptions (transcription)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_date ON transcriptions (date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_time ON transcriptions (time)")

# Commit the changes and close the connection
conn.commit()
conn.close()