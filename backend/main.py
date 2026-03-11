from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.notes_router import router as notes_router
from routers.folders_router import router as folders_router
from routers.chat_router import router as chat_router

app = FastAPI(title="NotaRAG API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes_router, prefix="/api")
app.include_router(folders_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}