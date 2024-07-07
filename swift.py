# Author: Elyes Rayane Melbouci
# Purpose: This script sets up a Flask application with Socket.IO and CORS support to load, index, and query documents using LangChain's document loaders and vector stores.

import os
import time
import threading
import json
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document
from pathlib import Path
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins (adjust if needed)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Path to the persistent directory
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
base_dir.mkdir(parents=True, exist_ok=True)

# Path to the JSON file
json_file_path = base_dir / 'all_texts.json'

# Persistent directory for the vector store
persist_directory = base_dir / 'vectoreDB'
persist_directory.mkdir(parents=True, exist_ok=True)

vectorstore = None  # Initialize vectorstore to None
retriever = None  # Initialize retriever to None

def load_and_index_documents_incrementally():
    global retriever  # Declare retriever as global
    global vectorstore  # Declare vectorstore as global

    print("Starting load_and_index_documents_incrementally")

    try:
        # Initialize the embedding model
        embedding_model = OllamaEmbeddings(model='nomic-embed-text')

        # Load existing vector store if it exists
        if persist_directory.exists():
            print(f"Loading existing vector store from {persist_directory}")
            vectorstore = Chroma(persist_directory=str(persist_directory), embedding_function=embedding_model)
        else:
            print("Creating a new vector store")
            vectorstore = Chroma(embedding_function=embedding_model, persist_directory=str(persist_directory))

        # Ensure the JSON file exists
        if not json_file_path.exists():
            print(f"JSON file not found: {json_file_path}")
            return None

        print(f"Loading JSON file from {json_file_path}")

        # Load new documents from JSON file
        with json_file_path.open('r') as f:
            transcriptions = json.load(f)

        print(f"Loaded {len(transcriptions)} transcriptions")

        docs = []
        for entry in transcriptions:
            date = entry["date"]
            for item in entry["entries"]:
                time = item["time"]
                text = item["text"]
                full_text = f"Date: {date}, Time: {time}\n{text}"
                docs.append(Document(page_content=full_text))

        print(f"Created {len(docs)} documents")

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=7500, chunk_overlap=2500)
        doc_splits = text_splitter.split_documents(docs)

        print(f"Split documents into {len(doc_splits)} chunks")

        # Add new documents to the existing vector store
        vectorstore.add_documents(doc_splits)
        vectorstore.persist()

        print("Documents added to vector store and persisted")

        retriever = vectorstore.as_retriever()
        print("Retriever initialized")
    except Exception as e:
        print(f"Error during load_and_index_documents: {e}")

# Load and index documents initially
print("Initial load and indexing")
load_and_index_documents_incrementally()

def summarize_day(date):
    print(f"Summarizing day for date: {date}")
    try:
        if not retriever:
            print("Retriever is not initialized")
            return "Retriever is not initialized. Ensure documents are loaded and indexed."

        query = f"Date: {date}"
        results = retriever.invoke(query)

        print(f"Found {len(results)} results for query: {query}")

        # Ensure results are of type Document
        if all(isinstance(doc, Document) for doc in results):
            input_docs = results
        else:
            input_docs = [Document(page_content=str(text)) for text in results if isinstance(text, str)]

        context = "\n\n".join(doc.page_content for doc in input_docs)

        return context

    except Exception as e:
        print(f"Error during summarize_day: {e}")
        return "There was an error summarizing the day."

@app.route('/')
def index():
    print("Received request on /")
    return "Chat application is running!"

@app.route('/index', methods=['POST'])
def index_endpoint():
    print("Received request on /index")
    try:
        data = request.json
        print("Data received for indexing")
        with json_file_path.open('w') as f:
            json.dump(data, f)
        print("Data written to JSON file")
        load_and_index_documents_incrementally()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error in /index endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/query', methods=['POST'])
def query_endpoint():
    print("Received request on /query")
    try:
        if not retriever:
            print("Retriever is not initialized")
            return jsonify({"status": "error", "message": "Retriever is not initialized. Ensure documents are loaded and indexed."}), 500

        query_text = request.json.get('query')
        print(f"Query received: {query_text}")
        results = retriever.invoke(query_text)
        context = "\n\n".join(doc.page_content for doc in results)
        
        # Generate a response based on the context
        response_text = f"The context is: {context}. Your query was: {query_text}. Here is the response based on the context."
        print("Query processed successfully")

        return jsonify({"results": [response_text]}), 200
    except Exception as e:
        print(f"Error in /query endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def periodic_reload(interval=1800):
    while True:
        print(f"Periodic reload every {interval} seconds")
        time.sleep(interval)
        load_and_index_documents_incrementally()

# Start the periodic reloading in a separate thread
print("Starting periodic reload thread")
thread = threading.Thread(target=periodic_reload, daemon=True)
thread.start()

if __name__ == '__main__':
    print("Server is up and running!")
    app.run(host='0.0.0.0', port=8005, debug=False)