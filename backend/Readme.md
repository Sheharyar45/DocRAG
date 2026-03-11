# 🧠 RAG Notetaking App - Backend (FastAPI)

This is the backend for our RAG-based note-taking application, built with **FastAPI**, **Supabase**, and **LangChain**.

## 🚀 Tech Stack
- **FastAPI** – backend framework  
- **Supabase** – authentication + Postgres database  
- **LangChain + AWS Bedrock** – AI/RAG  
- **Pinecone** – vector search (semantic retrieval)  

## 📦 Setup Instructions

1. cd backend
2. python3 -m venv venv
source venv/bin/activate

3. pip install -r requirements.txt
ollama pull qwen3:8b

4. uvicorn main:app --reload (make sure to run this from outside the backend directory)

---

database.py exports a client connection to supabase which can later be used by other parts of the backend.
main.py contains all the routers within it to redirect as required.
routers/ contains all the routers for different functions. These will be imported into main
   notes_router.py inclues all the functions that have to interact with the notes and their functions.