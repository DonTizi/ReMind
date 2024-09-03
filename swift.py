import logging
from pathlib import Path
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.schema import Document
from datetime import datetime, timedelta
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

base_dir = Path.home() / 'Library' / 'Application Support' / 'RemindEnchanted'
persist_directory = base_dir / 'vectoreDB'
persist_directory.mkdir(parents=True, exist_ok=True)

embedding_model = OllamaEmbeddings(model='nomic-embed-text')
llm = Ollama(model="llama3.1")
vectorstore = None
retriever = None
qa_chain = None

def initialize_vectorstore():
    global vectorstore, retriever, qa_chain
    try:
        if persist_directory.exists():
            logging.info("Loading existing vector store")
            vectorstore = Chroma(persist_directory=str(persist_directory), embedding_function=embedding_model)
            logging.info("Existing vector store loaded successfully")
        else:
            logging.info("Creating new vector store")
            vectorstore = Chroma(embedding_function=embedding_model, persist_directory=str(persist_directory))
            logging.info("New vector store created successfully")
        
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
        logging.info("Retriever and QA chain initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing vector store: {e}", exc_info=True)

def add_new_document(text, metadata):
    global vectorstore
    try:
        doc = Document(page_content=text, metadata=metadata)
        vectorstore.add_documents([doc])
        vectorstore.persist()
        logging.info("New document added to the vector store")
    except Exception as e:
        logging.error(f"Error adding new document: {e}", exc_info=True)

def classify_question(question):
    prompt = f"""Determine if the following question requires searching a knowledge base about the user's personal information and activities, or if it can be answered with general knowledge.

Question: {question}

If the question is about the user's personal information, activities, or anything that would require searching a personal knowledge base, respond with "SEARCH_REQUIRED".
If the question can be answered with general knowledge or does not require personal information, respond with "GENERAL_KNOWLEDGE".

Response:"""

    response = llm(prompt)
    return "SEARCH_REQUIRED" in response

def determine_time_range(question):
    prompt = f"""Analyze the following question and determine the time range it refers to.

Question: {question}

Respond with one of the following:
- TODAY: if the question refers to today or the current day
- YESTERDAY: if the question refers to yesterday
- WEEK: if the question refers to the current week or the past 7 days
- MONTH: if the question refers to the current month or the past 30 days
- ALL: if no specific time range is mentioned or if it refers to a longer period

Response:"""

    response = llm(prompt).strip().upper()
    return response if response in ["TODAY", "YESTERDAY", "WEEK", "MONTH"] else "ALL"

def get_date_range(time_range):
    today = datetime.now().date()
    if time_range == "TODAY":
        return today, today
    elif time_range == "YESTERDAY":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif time_range == "WEEK":
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week, today
    elif time_range == "MONTH":
        start_of_month = today.replace(day=1)
        return start_of_month, today
    else:
        return None, None  # For "ALL" or undefined ranges

def filter_documents_by_date(docs, start_date, end_date):
    if start_date is None or end_date is None:
        return docs
    return [
        doc for doc in docs 
        if start_date <= datetime.strptime(doc.metadata.get('date', '1970-01-01'), '%Y-%m-%d').date() <= end_date
    ]

@app.route('/')
def index():
    return "Chat application is running!"

@app.route('/add', methods=['POST'])
def add_document():
    data = request.json
    text = data.get('text')
    metadata = data.get('metadata', {})
    if not text:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    
    # Ensure the metadata includes the current date
    metadata['date'] = datetime.now().strftime('%Y-%m-%d')
    
    add_new_document(text, metadata)
    return jsonify({"status": "success", "message": "Document added successfully"}), 200

@app.route('/query', methods=['POST'])
def query_endpoint():
    if not qa_chain or not llm:
        return jsonify({"status": "error", "message": "QA chain or LLM not initialized. Check server logs for details."}), 500

    query_text = request.json.get('query')
    try:
        if classify_question(query_text):
            # Question requires searching the knowledge base
            time_range = determine_time_range(query_text)
            start_date, end_date = get_date_range(time_range)
            relevant_docs = retriever.invoke(query_text)
            filtered_docs = filter_documents_by_date(relevant_docs, start_date, end_date)
            
            if filtered_docs:
                # Generate a response that interprets what you might have been doing
                context = "\n".join([doc.page_content for doc in filtered_docs])
                ai_response = qa_chain.run(f"Given the following context: \n\n{context}\n\n Answer the question: '{query_text}' by interpreting what the user was likely doing with this information. Answer specifically the question about the specific subject with the context you have and nothing else.")
                ai_response = ai_response
            else:
                ai_response = f"I couldn't find any relevant information for the specified time range ({time_range.lower()} - {start_date} to {end_date}). Could you please rephrase your question or specify a different time range?"
            
            context = [doc.page_content for doc in filtered_docs]
        else:
            # Question can be answered with general knowledge
            ai_response = llm(query_text)
            context = []

        return jsonify({
            "status": "success",
            "results": [ai_response],
            "context": context
        }), 200
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        return jsonify({"status": "error", "message": "An error occurred while processing the query."}), 500

if __name__ == '__main__':
    initialize_vectorstore()
    logging.info("Server is starting...")
    socketio.run(app, host='0.0.0.0', port=8005, debug=False)
