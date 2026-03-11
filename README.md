# DocRAG – AI-Powered Note Management and Semantic Search Platform

> Helping bussinesses store, organize, and *intelligently* retrieve their notes using Retrieval-Augmented Generation (RAG) and semantic search.

---

## 🌟 Overview

**DocRAG** is a modern web-based note-taking platform that blends **AI-powered semantic search**, **contextual retrieval**, and **RAG-based summarization** to help users easily find and interact with their notes.

Unlike traditional keyword search, DocRAG understands the *meaning* behind your queries using **vector embeddings**.  
You can ask questions like:  
> “Find my notes about machine learning optimization techniques.”  
and DocRAG will return contextually relevant notes — not just text matches.

---

## ✨ Core Features

### 📝 User Authentication & Profiles
- Secure sign-up, login, logout via **Firebase** or **NextAuth.js**
- **Google/GitHub OAuth** for quick login  
- User-specific note storage & isolation

### 🗂️ Note Creation & Management
- Create, edit, delete, and organize notes (with folder support)  
- Rich text editor with **Markdown** support  
- Auto-save and version history  
- Custom **tagging system** for topics

### 🔍 Semantic Search (Core Feature)
- Notes embedded into a **vector database** (e.g., Pinecone / ChromaDB)
- Query notes using **natural language**
- Search results ranked by **semantic similarity**
- Highlights relevant note segments

### 🧠 RAG (Retrieval-Augmented Generation)
- When searching, relevant notes are retrieved and passed to an **LLM**
- Users can **chat with their notes**:
  > “Summarize my notes on React Hooks.”
- Uses **LangChain** (Retriever → LLMChain → Output)
- Local or API-based LLMs (Ollama / GPT / Claude / Bedrock)

### 📁 Topic Detection & Auto-Tagging
- AI automatically detects topics in each note
- Suggested tags are editable by users

### 🎨 UI/UX Design
- Built with **React + TailwindCSS + ShadCN UI**
- Clean, responsive dashboard  
- Dark/light mode  
- **Framer Motion** animations for smooth transitions

---

## 🚀 Future / Optional Features
- 🪄 **Smart Summaries:** Summarize all notes in a folder or topic  
- 🗣️ **Voice-to-Text Notes:** Speech-to-text note input  
- 🌐 **Cross-Device Sync:** Web, desktop, mobile sync  
- 🧷 **Collaborative Notes:** Share with teammates  
- 📊 **Insights Dashboard:** Topic trends & analytics  
- 💾 **Offline Mode:** Store notes locally (IndexedDB)  
- 🧩 **Quiz Generator:** Auto-generate study questions  
- 🧠 **AI Note Enrichment:** Suggest improvements or add info to notes  

---

## 🧰 Tech Stack

### Frontend
- **Framework:** React (HTML/CSS/JS)  
- **Styling:** TailwindCSS + ShadCN UI  
- **Animations:** Framer Motion  
- **State Management:** Redux Toolkit  

### Backend
- **Framework:** FastAPI (Python)  
- **Database:** PostgreSQL / MySQL (via Supabase or AWS RDS)  
- **Vector DB:** Pinecone / ChromaDB / AWS OpenSearch  
- **Authentication:** Firebase Auth / NextAuth.js  
- **Deployment:** Vercel (frontend) + Render (backend)  

### LLM & RAG Integration
- **LangChain** for orchestration  
- **Embeddings:** OpenAI / Cohere / Amazon Titan  
- **LLMs:** OpenAI GPT / Claude / Llama 3 / Ollama (local)  
- **Retrieval:** RetrievalQA or custom retriever pipeline  

### DevOps & Tooling
- **Version Control:** Git + GitHub  
- **Testing:** Jest (frontend), Pytest (backend)  
- **CI/CD:** GitHub Actions + Docker  
- **Docs & PM:** GitHub Wiki / Jira / Notion  

---

## 🧩 RAG Pipeline Design (LangChain)

| Component | Description |
|------------|-------------|
| **Document Loader** | Loads notes from DB or S3 |
| **Text Splitter** | Splits long notes into manageable chunks |
| **Embedding Model** | Converts text into dense vectors |
| **Vector Store** | Stores embeddings (e.g., Pinecone) |
| **Retriever** | Fetches top-k similar note chunks |
| **LLMChain** | Summarizes or contextualizes retrieved notes |
| **Memory** | Stores chat context for “chat with your notes” feature |

**Example Flow:**  
> User: “Summarize my notes on AI ethics.”  
> System: → Embed query → Retrieve top-k notes → Send to LLM → Return summarized result

---

## 🗓️ Project Timeline (Rough)

| Phase | Duration | Goals |
|-------|-----------|-------|
| **Week 1** | Setup | Repo setup, tech stack setup, UI design (Figma) |
| **Week 2** | Frontend | Register/Login, Dashboard, Folder UI |
| **Week 3** | Backend | DB schema, FastAPI setup, authentication |
| **Week 4** | CRUD | Note creation/editing, folder save |
| **Week 5** | Semantic Search | Vector DB + search page |
| **Week 6** | RAG Integration | LLM summarization + chatbot |
| **Week 7** | UI Polish & Testing | Animations, dark mode, tests |
| **Week 8** | Deployment | Deploy + docs |
| **Week 9+** | Optional | Auto-tagging, analytics, offline mode |

*(Timeline is flexible depending on exams/assignments.)*

---

## 👥 Roles & Responsibilities
TBD — Team leads and contributors to define core tasks (frontend, backend, AI pipeline, DevOps).

---

## 🔄 Collaboration & Workflow
- **Task Tracking:** GitHub Projects / Jira Board  
- **Weekly Standups:** 1 short meeting (e.g., Saturday)  
- **Branching:** No direct commits to `main`  
- **Code Reviews:** PRs must be peer-reviewed  
- **Docs:** Keep README & Jira updated weekly  

---

## 🧩 Maintainers
Maintained by the **NotaRAG Team**  
Part of the [CREATE UofT](https://github.com/CREATE-UofT) Project Ecosystem
