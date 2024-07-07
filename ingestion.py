# Author: Elyes Rayane Melbouci
# Purpose: This script loads JSON data, fetches new entries from a SQLite database, processes and groups the new data by date, updates existing JSON data, and marks entries as processed in the database.

import json
import sqlite3
import os
import logging
from collections import defaultdict
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def load_json(file_path):
    """Load JSON data from a file if it exists."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            logging.debug(f"Loading JSON data from {file_path}")
            return json.load(file)
    return []

def save_json(file_path, data):
    """Save JSON data to a file."""
    with open(file_path, 'w') as file:
        logging.debug(f"Saving JSON data to {file_path}")
        json.dump(data, file, indent=4)

def fetch_new_entries(db_path):
    """Fetch new entries from the database where processed is 0."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, metadata, date, time FROM images WHERE processed = 0")
    new_entries = cursor.fetchall()
    conn.close()
    logging.debug(f"Fetched new entries: {new_entries}")
    return new_entries

def update_processed_entries(db_path, ids):
    """Update entries as processed in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.executemany("UPDATE images SET processed = 1 WHERE id = ?", [(id,) for id in ids])
    conn.commit()
    conn.close()
    logging.debug(f"Updated entries as processed: {ids}")

# Define file and database paths
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
base_dir.mkdir(parents=True, exist_ok=True)

new_texts_path = base_dir / 'new_texts.json'
all_texts_path = base_dir / 'all_texts.json'
db_path = base_dir / 'regular_data.db'

# Load existing JSON data from all_texts.json
all_texts_data = load_json(all_texts_path)

# Fetch new entries from the database
new_entries = fetch_new_entries(db_path)

# Initialize the dictionary to group new data by date
new_grouped_data = defaultdict(list)

# Add new entries to the dictionary
for entry in new_entries:
    if len(entry) == 4 and entry[2] and entry[3]:
        new_grouped_data[entry[2]].append({'time': entry[3], 'text': entry[1]})
    else:
        logging.error(f"Malformed or missing entry: {entry}")

# Convert the dictionary to a list of dictionaries
new_json_data = [{'date': date, 'entries': entries} for date, entries in new_grouped_data.items()]

# Add new entries to all_texts_data
for date, entries in new_grouped_data.items():
    existing_entry = next((item for item in all_texts_data if item['date'] == date), None)
    if existing_entry:
        existing_entry['entries'].extend(entries)
    else:
        all_texts_data.append({'date': date, 'entries': entries})

# Save new data to new_texts.json (overwrite old data)
save_json(new_texts_path, new_json_data)

# Save complete data to all_texts.json
save_json(all_texts_path, all_texts_data)

# Mark entries as processed in the database
update_processed_entries(db_path, [entry[0] for entry in new_entries])