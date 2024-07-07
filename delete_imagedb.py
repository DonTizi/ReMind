# Author: Elyes Rayane Melbouci
# Purpose: This script connects to a SQLite database and deletes specific records from the 'images' table based on their IDs.

import sqlite3
from pathlib import Path

# Define the database path
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
base_dir.mkdir(parents=True, exist_ok=True)
db_path = base_dir / 'regular_data.db'

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# To delete specific records, you need to know their IDs or some unique identifier.
# For example, to delete images with specific IDs:
# Loop through the list and delete each entry
for image_id in range(1, 200):
    cursor.execute("DELETE FROM images WHERE id = 1", (image_id,))

# Commit the changes
conn.commit()

# Close the connection
conn.close()