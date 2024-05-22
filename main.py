import os
import subprocess
import threading
import time
import json

# Obtenir le répertoire de base du projet
base_dir = os.path.dirname(__file__)

# Chemin vers la base de données regular_db
regular_db_path = os.path.join(base_dir, 'memory_capture', 'database_management', 'regular_db.db')

# Chemins des fichiers JSON
all_texts_path = os.path.join(base_dir, 'memory_capture', 'vectore', 'all_texts.json')
new_texts_path = os.path.join(base_dir, 'memory_capture', 'vectore', 'new_texts.json')

# Script pour créer la base de données regular_db si elle n'existe pas
regular_db_script = os.path.join(base_dir, 'memory_capture', 'database_management', 'Regular_database.py')

# Scripts à exécuter
scripts = {
    "image_record": os.path.join(base_dir, 'memory_capture', 'record_photo.py'),
    "pipeline": os.path.join(base_dir, 'memory_capture', 'database_management', 'pipeline_db.py'),
    "ingestion": os.path.join(base_dir, 'memory_capture', 'database_management', 'ingestion.py'),
    "adding_vectore": os.path.join(base_dir, 'memory_capture', 'vectore', 'adding_vectore.py'),
    "indexing": os.path.join(base_dir, 'memory_capture', 'vectore', 'indexing.py')
}

# Vérifier et créer les fichiers JSON s'ils n'existent pas
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

if not os.path.exists(new_texts_path):
    with open(new_texts_path, 'w') as f:
        json.dump([], f)

# Vérifier l'existence de la base de données regular_db et lancer le script si elle n'existe pas
if not os.path.exists(regular_db_path):
    subprocess.call(['python', regular_db_script])

# Exécution des scripts d'enregistrement audio, d'image et du pipeline
for script in ["image_record", "pipeline"]:
    threading.Thread(target=subprocess.call, args=(['python', scripts[script]],)).start()

subprocess.call(['python', scripts["indexing"]])

# Fonction pour exécuter l'ingestion, l'ajout de vecteurs et l'indexation toutes les 2 minutes
def pipeline():
    while True:
        # Exécution du script d'ingestion
        subprocess.call(['python', scripts["ingestion"]])

        # Exécution du script d'ajout de vecteurs
        subprocess.call(['python', scripts["adding_vectore"]])

        # Attente de 2 minutes
        time.sleep(120)  # Attente de 2 minutes (120 secondes)

# Démarrage du pipeline
threading.Thread(target=pipeline).start()
