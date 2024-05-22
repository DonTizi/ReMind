# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from flask_cors import CORS
import json
from langchain.schema import Document  # Import the Document class
from langchain.chains.summarize import load_summarize_chain
import threading
import time
import os

app = Flask(__name__)
CORS(app)  # Enable CORS
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow all origins (adjust if needed)

# Initialize the model
model_local = ChatOllama(model="recallAI")

# Path to the JSON file
json_file_path = 'memory_capture/vectore/all_texts.json'
persist_directory = 'memory_capture/vectore/vectoreDB'

def load_and_index_documents():
    global retriever  # Declare retriever as global
    try:
        print("Loading and indexing documents...")

        # 1. Load and extract texts from the JSON file
        with open(json_file_path, 'r') as f:
            transcriptions = json.load(f)

        docs = []
        for entry in transcriptions:
            date = entry["date"]
            for item in entry["entries"]:
                time = item["time"]
                text = item["text"]
                # Combine date, time and text for context
                full_text = f"Date: {date}, Time: {time}\n{text}"
                docs.append(Document(page_content=full_text))  # Use Document class

        # Print loaded documents for debugging
        print(f"Loaded documents: {len(docs)}")

        # 2. Split texts into chunks
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=500, chunk_overlap=100)
        doc_splits = text_splitter.split_documents(docs)

        # Print number of documents loaded
        print(f"Number of documents loaded: {len(docs)}")

        # Print number of chunks created
        print(f"Number of chunks created: {len(doc_splits)}")

        # 3. Store the chunks in the Chroma vector store
        print("Storing documents in the Chroma vector store...")
        global vectorstore
        vectorstore = Chroma.from_documents(
            documents=doc_splits,
            collection_name="local_text_chroma",
            embedding=OllamaEmbeddings(model='nomic-embed-text'),
            persist_directory=persist_directory  # Add this line to persist the vector DB
        )

        retriever = vectorstore.as_retriever()

        # Print some embeddings for debugging
        for i, doc in enumerate(doc_splits[:5]):  # Just print the first 5 for brevity
            embedding = vectorstore._embedding_function.embed_query(doc.page_content)
            print(f"Embedding for document chunk {i}: {embedding[:5]}...")  # Print the first 5 dimensions for brevity
    except Exception as e:
        print(f"Error during load_and_index_documents: {e}")

# Load and index documents initially
load_and_index_documents()

# Setup the RAG template and chain
rag_template = """
Given the following Digital activity, answer the question as accurately as possible with details:
{context}

Question: {question}
"""
rag_prompt = ChatPromptTemplate.from_template(rag_template)
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | rag_prompt
    | model_local
    | StrOutputParser()
)

# Setup the RAG template and chain for summarization
rag_summarize_template = """Based on the following Digital activity:
{context}
Provide a summary of the day's activities, what he did and how, with a bulletproof list of his activity  and do not mention the activity as a text or a json but as a digital activity:
"""
rag_summarize_prompt = ChatPromptTemplate.from_template(rag_summarize_template)
rag_summarize_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | rag_summarize_prompt
    | model_local
    | StrOutputParser()
)

def summarize_day(date):
    try:
        query = f"Date: {date}"
        results = retriever.invoke(query)

        # Print retrieved documents for debugging
        print(f"Retrieved documents: {results}")

        # Ensure results are of type Document
        if all(isinstance(doc, Document) for doc in results):
            input_docs = results
        else:
            input_docs = [Document(page_content=str(text)) for text in results if isinstance(text, str)]

        # Print input documents for debugging
        print(f"Input documents for summarization: {input_docs}")

        # Set up the context for the RAG chain
        context = "\n\n".join(doc.page_content for doc in input_docs)

        # Run the RAG summarization chain
        summary_stream = rag_summarize_chain.stream({"context": context, "question": "Provide a summary of the day's activities:"})

        def summary_generator():
            for chunk in summary_stream:
                yield chunk

        return summary_generator()

    except Exception as e:
        print(f"Error during summarize_day: {e}")
        return iter([("There was an error summarizing the day.", True, False)])  # Return a single-chunk iterator with error message

@app.route('/')
def index():
    return "Chat application is running!"

@socketio.on('send_message')
def handle_message(data):
    user_query = data['message']

    def generate_response():
        try:
            if "summarize my day" in user_query.lower():
                # Extract the date from the user query, assume date is provided in the query
                date = "16 May 2024"  # Example date, extract the actual date from the user query
                # Initial typing indicator
                socketio.emit('response_message', {'message': "", 'isFirstChunk': True, 'isIncomplete': True})
                socketio.sleep(0)
                summary_stream = summarize_day(date)
                print(f"Emitting summary...")  # Debugging print

                is_first_chunk = True
                for chunk in summary_stream:
                    socketio.emit('response_message', {'message': chunk, 'isFirstChunk': is_first_chunk, 'isIncomplete': True})
                    socketio.sleep(0)  # Adjust delay for typing speed (optional)
                    is_first_chunk = False

                # Signal end of summary
                socketio.emit('response_message', {'message': "", 'isFirstChunk': False, 'isIncomplete': False})
                return

            response_stream = rag_chain.stream(user_query)

            # Initial typing indicator
            socketio.emit('response_message', {'message': "", 'isFirstChunk': True, 'isIncomplete': True})
            socketio.sleep(0)

            for chunk in response_stream:
                socketio.emit('response_message', {'message': chunk, 'isFirstChunk': False, 'isIncomplete': True})
                socketio.sleep(0)  # Adjust delay for typing speed (optional)

                # Print the chunk for debugging
                print(f"Chunk: {chunk}")

            # Signal end of response
            socketio.emit('response_message', {'message': "", 'isFirstChunk': False, 'isIncomplete': False})
        except Exception as e:
            print(f"Error during generate_response: {e}")

    socketio.start_background_task(generate_response)

def periodic_reload(interval=600):
    while True:
        time.sleep(interval)
        load_and_index_documents()

# Start the periodic reloading in a separate thread
thread = threading.Thread(target=periodic_reload, daemon=True)
thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
