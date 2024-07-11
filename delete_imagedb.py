import sqlite3
from pathlib import Path
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
db_path = base_dir / 'regular_data.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Supprimer les entrées traitées et plus anciennes que 7 jours
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("DELETE FROM images WHERE processed = 1 AND date < ?", (seven_days_ago,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    logging.info(f"Suppression terminée. {deleted_count} images ont été supprimées.")

except sqlite3.Error as e:
    logging.error(f"Une erreur SQLite est survenue : {e}")

finally:
    if conn:
        conn.close()
        logging.info("Connexion à la base de données fermée.")

logging.info("Opération de suppression terminée.")