import json
import sqlite3
import os
import logging
from collections import defaultdict

# Configuration de logging
logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log'),
                    level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def fetch_new_entries(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, metadata, date, time FROM images WHERE processed = 0")
    new_entries = cursor.fetchall()
    conn.close()
    return new_entries

def update_processed_entries(db_path, ids):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executemany("UPDATE images SET processed = 1 WHERE id = ?", [(id,) for id in ids])
    conn.commit()
    conn.close()

# Définir les chemins des fichiers et de la base de données
new_texts_path = os.path.join(os.path.dirname(__file__), '..','vectore', 'new_texts.json')
all_texts_path = os.path.join(os.path.dirname(__file__), '..','vectore', 'all_texts.json')
db_path = 'memory_capture/database_management/regular_data.db'

# Charger les données JSON existantes de all_texts.json
all_texts_data = load_json(all_texts_path)

# Récupérer les nouvelles entrées de la base de données
new_entries = fetch_new_entries(db_path)

# Initialiser le dictionnaire pour grouper les nouvelles données par date
new_grouped_data = defaultdict(list)

# Ajouter les nouvelles entrées au dictionnaire
for entry in new_entries:
    if len(entry) == 4 and entry[2] and entry[3]:
        new_grouped_data[entry[2]].append({'time': entry[3], 'text': entry[1]})
    else:
        logging.error(f"Entrée manquante ou mal formée: {entry}")

# Convertir le dictionnaire en une liste de dictionnaires
new_json_data = [{'date': date, 'entries': entries} for date, entries in new_grouped_data.items()]

# Ajouter les nouvelles entrées à all_texts_data
for date, entries in new_grouped_data.items():
    existing_entry = next((item for item in all_texts_data if item['date'] == date), None)
    if existing_entry:
        existing_entry['entries'].extend(entries)
    else:
        all_texts_data.append({'date': date, 'entries': entries})

# Enregistrer les nouvelles données dans new_texts.json (écraser les anciennes)
save_json(new_texts_path, new_json_data)

# Enregistrer les données complètes dans all_texts.json
save_json(all_texts_path, all_texts_data)

# Mettre à jour les entrées comme traitées dans la base de données
update_processed_entries(db_path, [entry[0] for entry in new_entries])

logging.info(f"{len(new_entries)} nouvelles entrées ajoutées aux fichiers JSON et mises à jour comme traitées dans la base de données.")
