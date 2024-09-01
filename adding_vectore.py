import json
import os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define file and database paths
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
base_dir.mkdir(parents=True, exist_ok=True)

json_file_path = base_dir / 'new_texts.json'
processed_ids_path = base_dir / 'processed_ids.json'
persist_directory = base_dir / 'vectoreDB'

def load_processed_ids():
    if processed_ids_path.exists():
        with open(processed_ids_path, 'r') as f:
            return set(json.load(f))
    return set()

def save_processed_ids(processed_ids):
    with open(processed_ids_path, 'w') as f:
        json.dump(list(processed_ids), f)

def process_new_documents():
    processed_ids = load_processed_ids()
    embedding_model = OllamaEmbeddings(model='nomic-embed-text')
    
    # Load or create vectorstore
    if persist_directory.exists():
        logging.info("Loading existing vector store")
        vectorstore = Chroma(persist_directory=str(persist_directory), embedding_function=embedding_model)
    else:
        logging.info("Creating new vector store")
        vectorstore = Chroma(embedding_function=embedding_model, persist_directory=str(persist_directory))

    # Load and process new documents
    if not json_file_path.exists():
        logging.warning(f"JSON file not found: {json_file_path}")
        return

    with open(json_file_path, 'r') as f:
        data = json.load(f)

    new_docs = []
    new_ids = set()
    for entry in data:
        date = entry['date']
        for item in entry['entries']:
            doc_id = f"{date}-{item['time']}"
            if doc_id not in processed_ids:
                text = f"Date: {date}, Time: {item['time']}\n{item['text']}"
                new_docs.append(Document(page_content=text, metadata={"id": doc_id, "date": date, "time": item['time']}))
                new_ids.add(doc_id)

    if new_docs:
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=4500, chunk_overlap=1000)
        doc_splits = text_splitter.split_documents(new_docs)

        # Add new documents to vectorstore
        vectorstore.add_documents(doc_splits)
        vectorstore.persist()

        # Update processed IDs
        processed_ids.update(new_ids)
        save_processed_ids(processed_ids)

        logging.info(f"Processed and added {len(new_docs)} new documents to the vector store")
    else:
        logging.info("No new documents to process")

    # Optional: Remove the JSON file after processing
    # os.remove(json_file_path)

if __name__ == "__main__":
    process_new_documents()