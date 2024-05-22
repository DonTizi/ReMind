import os
import time
import logging
import sqlite3
import easyocr
from PIL import Image, ExifTags
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
from collections import defaultdict

# Configuration de logging
logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s: %(message)s')

# Chemins vers les dossiers principaux
chemin_images = 'screenshots'
print(chemin_images)
chemin_transcriptions = 'memory_capture/transcriptions'
print(chemin_transcriptions)
# Chemin du fichier JSON pour stocker les données
json_output_path = 'memory_capture/vectore/new_texts.json'
print(json_output_path)
# Initialisation du lecteur OCR (EasyOCR)
reader = easyocr.Reader(['fr', 'en'])

# Initialiser le fichier JSON s'il n'existe pas
if not os.path.exists(json_output_path):
    with open(json_output_path, 'w') as json_file:
        json.dump([], json_file)

# Dictionnaire pour mettre en cache les fichiers déjà traités
processed_files = {}

def wait_for_file_to_finish(file_path):
    """Attendre que la taille du fichier ne change plus."""
    size = -1
    while size != os.path.getsize(file_path):
        size = os.path.getsize(file_path)
        time.sleep(0.5)

def extract_date_from_image(image_path):
    """Extraire la date et l'heure à partir des métadonnées de l'image."""
    try:
        image = Image.open(image_path)
        exif = image._getexif()
        if exif:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                if decoded == "DateTime":
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction de la date de l'image {image_path}: {e}")
    return None

def save_to_db_and_json(image_data, json_output_path):
    """Sauvegarder les données dans la base de données SQLite et le fichier JSON."""
    try:
        db_path = 'memory_capture/database_management/regular_data.db'
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()

        # Vérifier si la table 'images' existe, sinon la créer
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

        # Insertion dans la base de données SQLite
        cursor.execute("INSERT INTO images (image, metadata, date, time, processed) VALUES (?, ?, ?, ?, 0)", 
                       (image_data['image'], image_data['text'], image_data['date'], image_data['time']))
        conn.commit()
        logging.debug(f"Données insérées dans la base de données : {image_data}")

        # Charger les données existantes
        if os.path.exists(json_output_path) and os.path.getsize(json_output_path) > 0:
            with open(json_output_path, 'r') as json_file:
                transcriptions = json.load(json_file)
        else:
            transcriptions = []

        # Consolider les données par date
        grouped_transcriptions = defaultdict(list)
        for entry in transcriptions:
            grouped_transcriptions[entry['date']].append({"time": entry['time'], "text": entry['text']})
        
        # Ajouter la nouvelle transcription
        grouped_transcriptions[image_data['date']].append({"time": image_data['time'], "text": image_data['text']})

        # Préparer les données pour sauvegarde
        consolidated_transcriptions = [{"date": date, "entries": entries} for date, entries in grouped_transcriptions.items()]

        # Sauvegarder les données mises à jour
        with open(json_output_path, 'w') as json_file:
            json.dump(consolidated_transcriptions, json_file, indent=4)
        
        logging.info(f"Image et texte insérés avec succès dans la base de données et le fichier JSON.")

    except sqlite3.Error as e:
        logging.error(f"Erreur lors de l'insertion dans la base de données : {e}")
    finally:
        conn.close()

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            observer.schedule(FileHandler(), event.src_path, recursive=False)
        else:
            self.handle_file(event.src_path)

    def handle_file(self, file_path):
        logging.info(f"Handling file: {file_path}")
        if file_path in processed_files:
            logging.info(f"File already processed: {file_path}")
            return

        try:
            wait_for_file_to_finish(file_path)

            if chemin_images in file_path:
                with Image.open(file_path) as img:
                    logging.info(f"Extracting text from image: {file_path}")
                    text = reader.readtext(img, detail=0, paragraph=True)
                    logging.debug(f"Text extracted: {text}")
                    text = ' '.join(text)

                    # Filtrer le texte pour éliminer le bruit
                    filtered_text = ' '.join([word for word in text.split() if len(word) > 1])
                    logging.debug(f"Filtered text: {filtered_text}")

                    date_time = extract_date_from_image(file_path)
                    if not date_time:
                        date_time = datetime.now()
                    date_str = date_time.strftime("%d %b %Y")
                    time_str = date_time.strftime("%H:%M")

                    image_data = {
                        "image": img.tobytes(),
                        "date": date_str,
                        "time": time_str,
                        "text": filtered_text
                    }

                    logging.info(f"Saving data to DB and JSON for file: {file_path}")
                    save_to_db_and_json(image_data, json_output_path)

                    # Marquer le fichier comme traité
                    processed_files[file_path] = True
        except Exception as e:
            logging.error(f"Erreur lors de l'insertion du fichier {file_path}: {e}")

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            MyHandler().handle_file(event.src_path)

# Observer pour les dossiers principaux (qui va détecter les nouveaux dossiers de date)
observer = Observer()
observer.schedule(MyHandler(), chemin_images, recursive=True)
observer.schedule(MyHandler(), chemin_transcriptions, recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)  # Eviter une boucle infinie trop gourmande
except KeyboardInterrupt:
    observer.stop()
    logging.info("Surveillance des dossiers arrêtée.")
observer.join()
