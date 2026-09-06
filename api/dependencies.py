from fastapi import Request
from database.database import SessionLocal


def get_rag(request : Request):

    return request.app.state.rag


def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()    