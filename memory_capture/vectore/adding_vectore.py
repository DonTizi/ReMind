import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama

# Initialize the model
model_local = ChatOllama(model="recallAI")

# Path to the JSON file
json_file_path = 'memory_capture/vectore/new_texts.json'

# 1. Load and Split Text Files
print("Loading text files...")
text_files = [json_file_path]  # Replace with your file names
docs = []
for file in text_files:
    loader = TextLoader(file)
    loaded_docs = loader.load()
    docs.extend(loaded_docs)
    print(f"Loaded {len(loaded_docs)} documents from {file}")
    print(docs)

# Check number of loaded documents
print(f"Total documents loaded: {len(docs)}")

# 2. Split documents into chunks
print("Splitting documents into chunks...")
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=7500, chunk_overlap=100)
doc_splits = text_splitter.split_documents(docs)

# Check number of chunks created
print(f"Total chunks created: {len(doc_splits)}")
print("Chunks created:")
for chunk in doc_splits:
    print(chunk.page_content)

# 3. Convert documents to embeddings and store them
print("Converting documents to embeddings and storing them...")
persist_directory = 'memory_capture/vectore/vectoreDB'
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="local_text_chroma",  # Change collection name if needed
    embedding=OllamaEmbeddings(model='nomic-embed-text'),
    persist_directory=persist_directory  # Add this line to persist the vector DB
)

retriever = vectorstore.as_retriever()

print("Embeddings stored successfully.")
