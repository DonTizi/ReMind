# Author: Elyes Rayane Melbouci
# Purpose: This script loads text files, splits them into smaller segments, converts them into embeddings, and stores them in a vector database for efficient retrieval using language models.

import os
import sys
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from pathlib import Path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Initialize the model
model_local = ChatOllama(model="recallAI")

# Define file and database paths
base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
base_dir.mkdir(parents=True, exist_ok=True)

# Path to the JSON file
json_file_path = base_dir / 'new_texts.json'

# 1. Load and Split Text Files
text_files = [json_file_path]  # Replace with your file names
docs = []
for file in text_files:
    loader = TextLoader(file)
    loaded_docs = loader.load()
    docs.extend(loaded_docs)

# 2. Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=7500, chunk_overlap=100)
doc_splits = text_splitter.split_documents(docs)

# 3. Convert documents to embeddings and store them
persist_directory = base_dir / 'vectoreDB'
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="local_text_chroma",
    embedding=OllamaEmbeddings(model='nomic-embed-text'),
    persist_directory=str(persist_directory)  # Convert Path to string
)

retriever = vectorstore.as_retriever()