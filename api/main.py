import uuid
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi import (
    FastAPI,
    Depends, 
    UploadFile, 
    File, 
    HTTPException, 
    Response,
    Request
)
from contextlib import asynccontextmanager
from pathlib import Path
from sqlalchemy.orm import Session


from api.schemas import (
    ChatRequest, 
    ChatResponse, 
    ConversationsResponse, 
    MessageResponse,
    UserResponse,
    DocumentResponse
)
from auth.schemas import SignupRequest , LoginRequest 
from auth.security import hash_password , verify_password
from src.rag_initializer import initialize_rag
from src.rag_pipeline import process_query
from api.dependencies import get_rag
from src.config import DATA_FOLDER
from src.ingestion_pipeline import ingest_file
from src.chunk_store import get_user_chunk_from_store
from src.bm25_retriever import create_bm25_retriever
from src.config import SUPPORTED_EXTENSIONS
from src.hashing import calculate_file_hash
from src.vector_store import is_document_indexed , delete_document_chunks
from api.dependencies import get_db
from database.models import User , UserSession , Documents , Message
from auth.dependencies import get_current_user
from database.crud import (
    get_conversation,
    get_message_history,
    save_message,
    create_conversation,
    update_conversation_title,
    get_user_conversations,
    get_messages,
    create_user,
    get_user_by_email
)
from auth.session import create_session



@asynccontextmanager
async def lifespan(app : FastAPI):

    print("Starting FastApi application")

    app.state.rag = initialize_rag()

    print("RAG system loaded")

    yield

    print("Shutting down FastApi application")




app = FastAPI(lifespan=lifespan)



app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="templates")



@app.get("/")
def home(
    request : Request
):
    session_id = request.cookies.get("session_id")

    if session_id:
        return RedirectResponse(url = "/chat-page")

    return RedirectResponse(url = "/login")
    




@app.get("/chat-page")
def chat_page(
    request : Request,
    db : Session = Depends(get_db)
):
    session_id = request.cookies.get("session_id")

    if not session_id:
        return RedirectResponse(
            url = "/login",
            status_code = 303
        )

    session = db.query(UserSession).filter(
        UserSession.session_id == session_id
    ).first()

    if not session:
            return RedirectResponse(
            url="/login",
            status_code=303
        )

    if session.expires_at < datetime.utcnow():
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    
    response =  templates.TemplateResponse(
        request=request,
        name="chat.html"
    )

    response.headers["Cache-Control"] = "no-store"

    return response




@app.get(
        "/users/{user_id}",
        response_model = UserResponse
    )
def get_user(
        user_id : int,
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db)
):

    if user_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code = 404,
            detail = "User not Found"
        )

    return user





@app.post("/upload")
async def upload_file(
        file : UploadFile = File(...),
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db),
        rag = Depends(get_rag)
):

    safe_filename = Path(file.filename).name

    unique_filename = f"{uuid.uuid4()}_{safe_filename}"

    file_path = Path(DATA_FOLDER) / unique_filename

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:

        return {
            "message": f"Unsupported file type: {file_path.suffix}"
        }

    with open(file_path , "wb") as f:

        content = await file.read()

        f.write(content)

    file_hash = calculate_file_hash(file_path)    

    if is_document_indexed(
        rag["vector_store"],
        file_hash,
        current_user.id
    ):

        return {
            "file_name": file.filename,
            "message": "Document already indexed"
        }

    document = Documents(
        user_id = current_user.id,
        filename = safe_filename,
        file_path = str(file_path)
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        status = ingest_file(
            file_path,
            rag["vector_store"] ,
            current_user.id , 
            document.id , 
            safe_filename
        )

    except Exception as e:
        db.delete(document)
        db.commit()

        file_path.unlink(missing_ok=True)
        return {
            "message": f"Error indexing file: {e}"
        }

    if status == "indexed":

        user_chunks = get_user_chunk_from_store(
            rag["vector_store"],
            current_user.id
        )

        user_bm25 = create_bm25_retriever(
            user_chunks
        )

        rag["user_rag"][current_user.id] = {
            "chunks" : user_chunks,
            "bm25" : user_bm25
        }

        return {
            "file_name": file.filename,
            "message": "File uploaded and indexed Successfully"
        }

    if status == "duplicate":

        return {
            "file_name": file.filename,
            "message": "Document already indexed"
        }





@app.post("/chat" , response_model = ChatResponse)
def chat(
        request : ChatRequest ,
        rag = Depends(get_rag),
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db)
    ):

    if not request.query.strip():
        raise HTTPException(
            status_code = 400,
            detail = "Query Can not be empty"
        )

    user_id = current_user.id

    if request.conversation_id == None:

        conversation = create_conversation(
            db,
            user_id,
            "New Chat"
        )

    else:

        conversation = get_conversation(
            db,
            request.conversation_id,
            user_id
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                  detail="Conversation not found"
            )    

    conversation_id = conversation.id
    
    history = get_message_history(
        db,
        conversation_id
    ) 

    if(len(history) == 0):

        update_conversation_title(
            db,
            conversation_id,
            request.query
        )

        db.refresh(conversation)

    user_rag = rag["user_rag"].get(user_id)

    if not user_rag:
        raise HTTPException(
            status_code = 404,
            detail="No documents uploaded by this user"
        )

    vector_store = rag["vector_store"]
    reranker_model = rag["reranker_model"]
    llm = rag["llm"]
    query_rewriter = rag["query_rewriter"]
    chunks = user_rag["chunks"]
    bm25 = user_rag["bm25"]


    answer , sources = process_query(
        request.query,
        history,
        vector_store,
        chunks,
        bm25,
        reranker_model,
        llm,
        query_rewriter,
        user_id
    )    

    save_message(
        db,
        conversation_id,
        "user",
        request.query
    )

    save_message(
        db,
        conversation_id,
        "assistant",
        answer,
        citations = sources
    )

    return{
        "conversation_id" : conversation_id,
        "title": conversation.title,
        "answer" : answer,
        "sources" : sources
    }





@app.post("/conversations")
def create_new_conversation(
        current_user: User = Depends(get_current_user),
        db : Session = Depends(get_db)
):

    user_id = current_user.id

    conversation = create_conversation(
        db,
        user_id,
        "New Title"
    )

    return{
        "conversation_id" : conversation.id,
        "title" : conversation.title
    }





@app.get(
        "/conversations" , 
         response_model=list[ConversationsResponse]
        )
def get_all_conversations(
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db),
):

    user_id = current_user.id

    conversations = get_user_conversations(
        db,
        user_id
    )

    return conversations
    




@app.get(
        "/conversations/{conversation_id}/messages",
        response_model= list[MessageResponse]
    )
def get_conversation_messages(
        conversation_id : int,
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db)
):

    user_id = current_user.id

    conversation = get_conversation(
        db,
        conversation_id,
        user_id
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    messages = get_messages(
        db,
        conversation_id
    )

    return messages




@app.delete("/conversations/{conversation_id}")
def delete_conversation(
        conversation_id : int,
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db)
):

    conversation = get_conversation(
        db,
        conversation_id,
        current_user.id
    )

    if not conversation:

        raise HTTPException(
            status_code = 404,
            detail = "Conversation not found"
        )

    db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).delete()

    db.delete(conversation)
    db.commit()

    return{
        "message" : "Conversation deleted successfully"
    }




@app.post("/signup")
def signup(
        request : SignupRequest,
        db : Session = Depends(get_db),
):

    existing_user = get_user_by_email(
        db,
        request.email
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email Already Registered"
        )

    password_hash = hash_password(
        request.password
    )

    user = create_user(
        db,
        request.username,
        request.email,
        password_hash
    )

    return {
        "message": "User created successfully",
        "user_id": user.id
    }






@app.get("/login")
async def login_page(
        request : Request
):

    return templates.TemplateResponse(
        request = request,
        name = "login.html"
    )




@app.get("/signup")
async def signup_page(
        request : Request
):

    return templates.TemplateResponse(
        request = request,
        name = "signup.html"
    )





@app.post("/login")
def login(
        request : LoginRequest,
        response : Response,
        db : Session = Depends(get_db) 
):
    existing_user = get_user_by_email(
        db,
        request.email
    )

    if not existing_user:
        raise HTTPException(
            status_code = 401,
            detail="Invalid Email or Password"
        )

    if not verify_password(
        request.password,
        existing_user.password_hash
    ):
        raise HTTPException(
            status_code = 401,
            detail = "Invalid Email or Password"
        )

    new_session = create_session(
        db,
        existing_user.id
    )

    response.set_cookie(
        key = "session_id",
        value = new_session.session_id,
        httponly = True,
        secure = True,
        samesite = "lax"
    )

    return {
        "message": "User Login successfully"
    }




@app.post("/logout")
def logout(
        request : Request,
        response : Response,
        db : Session = Depends(get_db)
):

    session_id = request.cookies.get("session_id")

    if session_id:

        session = db.query(UserSession).filter(
            UserSession.session_id == session_id
            ).first()

        if session:

            db.delete(session)
            db.commit()

    response.delete_cookie("session_id")

    return {
        "message": "Logout successful"
    }        




@app.get(
        "/documents",
        response_model = list[DocumentResponse]
        )
def get_documents(
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db)
):

    documents = db.query(Documents).filter(
        Documents.user_id == current_user.id
    ).all()

    return documents




@app.get(
        "/documents/{document_id}",
        response_model = DocumentResponse
    )
def get_document_by_id(
        document_id : int,
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db) 
):

    document = db.query(Documents).filter(
        Documents.id == document_id,
        Documents.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code = 404,
            detail = "Document not found"
        )

    return document




@app.delete("/documents/{document_id}")
def delete_document(
        document_id : int,
        current_user : User = Depends(get_current_user),
        db : Session = Depends(get_db),
        rag = Depends(get_rag),
):

    document = db.query(Documents).filter(
        Documents.id == document_id,
        Documents.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(
            status_code = 404,
            detail = "Document not found"
        )

    try:

    # Delete chunks from Chroma
        delete_document_chunks(
            rag["vector_store"],
            document_id
        )

        # Delete physical file
        file_path = Path(document.file_path)

        if file_path.exists():
            file_path.unlink()

        # Delete database record
        db.delete(document)
        db.commit()

        # Rebuild this user's cached chunks + BM25
        user_chunks = get_user_chunk_from_store(
            rag["vector_store"], 
            current_user.id
        )

        if user_chunks :

            user_bm25 = create_bm25_retriever(user_chunks)

            rag["user_rag"][current_user.id] = {
                "chunks": user_chunks, 
                "bm25": user_bm25
                }

        else:

            rag["user_rag"].pop(current_user.id, None)    

    except Exception as e:

        db.rollback()

        print(
            f"Error deleting document {document_id}: {e}"
        )

        raise HTTPException(
            status_code = 500,
            detail = "Error deleting document"
        )
   
    return{
        "message": "Document deleted successfully"
    }    