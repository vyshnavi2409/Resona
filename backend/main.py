import os
import shutil
from typing import List, Tuple, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

from core.document_processor import process_document
from core.chunking import split_documents
from core.vector_store import add_documents_to_vector_store, clear_vector_store
from core.rag_pipeline import create_rag_chain, format_chat_history
from core.database import (
    create_session, get_all_sessions, get_session_messages, add_message,
    create_user, get_user_by_email, get_user_by_id
)
from core.auth import get_password_hash, verify_password, create_access_token, decode_access_token

app = FastAPI(title="RESONA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Auth Dependency
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# Auth Models
class UserCreate(BaseModel):
    fullname: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    chat_history: List[Tuple[str, str]] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str

@app.post("/register")
async def register(user: UserCreate):
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    user_id = create_user(user.fullname, user.email, hashed_password)
    return {"message": "User created successfully", "user_id": user_id}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "fullname": user["fullname"]}

@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "fullname": current_user["fullname"], "email": current_user["email"]}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), current_user: dict = Depends(get_current_user)):
    processed_files = []
    try:
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            documents = process_document(file_path)
            chunks = split_documents(documents)
            add_documents_to_vector_store(chunks)
            processed_files.append(file.filename)
            
        return {"message": "Files processed and indexed successfully.", "files": processed_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        session_id = request.session_id
        if not session_id:
            session_id = create_session(current_user["id"])

        db_messages = []
        try:
            db_messages = get_session_messages(session_id, current_user["id"])
        except PermissionError:
            raise HTTPException(status_code=403, detail="Not authorized to access this session")

        history_tuples = []
        human_msg = None
        for msg in db_messages:
            if msg["role"] == "user":
                human_msg = msg["content"]
            elif msg["role"] == "assistant" and human_msg is not None:
                history_tuples.append((human_msg, msg["content"]))
                human_msg = None
                
        rag_chain = create_rag_chain()
        formatted_history = format_chat_history(history_tuples)
        
        add_message(session_id, current_user["id"], "user", request.question)
        
        response = rag_chain.invoke({
            "input": request.question,
            "chat_history": formatted_history
        })
        
        answer = response["answer"]
        context_docs = response.get("context", [])
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in context_docs]))
        
        add_message(session_id, current_user["id"], "assistant", answer, sources)
        
        return ChatResponse(answer=answer, sources=sources, session_id=session_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
def list_sessions(current_user: dict = Depends(get_current_user)):
    return get_all_sessions(current_user["id"])

@app.post("/sessions")
def new_session(current_user: dict = Depends(get_current_user)):
    session_id = create_session(current_user["id"])
    return {"session_id": session_id}

@app.get("/sessions/{session_id}")
def get_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return get_session_messages(session_id, current_user["id"])
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

@app.delete("/clear")
def clear_db(current_user: dict = Depends(get_current_user)):
    try:
        clear_vector_store()
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return {"message": "Database and uploaded files cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
