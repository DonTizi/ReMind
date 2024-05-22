import sqlite3

# Connect to the database
conn = sqlite3.connect('regular_data.db')
cursor = conn.cursor()

# To delete a specific record, you need to know its ID or some unique identifier.
# For example, to delete an image with a specific ID:
  # Replace with the ID of the image you want to delete
# Loop through the list and delete each entry
for image_id in range(1,100):
    cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))

# Commit the changes
conn.commit()

# Close the connection
conn.close()
