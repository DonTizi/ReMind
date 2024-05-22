import sqlite3
import os

# Définir le chemin relatif pour la base de données
db_path = os.path.join(os.path.dirname(__file__), 'regular_data.db')

# Connexion à la base de données
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Créer la table pour les images avec les colonnes date et heure
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

# Créer la table pour les transcriptions avec les colonnes date et heure
cursor.execute('''
CREATE TABLE IF NOT EXISTS transcriptions (
    id INTEGER PRIMARY KEY,
    titre TEXT,
    transcription TEXT,
    date TEXT,
    time TEXT,
    autres_metadata TEXT
)
''')

# Ajouter des index pour optimiser les recherches
cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_metadata ON images (metadata)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_date ON images (date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_time ON images (time)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_transcription ON transcriptions (transcription)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_date ON transcriptions (date)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_time ON transcriptions (time)")

# Valider les modifications et fermer la connexion
conn.commit()
conn.close()
