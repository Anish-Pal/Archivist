from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from api.dependencies import get_db
from database.models import UserSession


def get_current_user(
        request : Request,
        db : Session = Depends(get_db)
):

    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(
            status_code = 401,
            detail = "Not authenticated"
        )

    session = db.query(UserSession).filter(
        UserSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(
            status_code = 401,
            detail = "Invalid session"
    )

    if session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code = 401,
            detail = "Session expired"
        )

    print("Session ID:", session_id)
    print("Session DB ID:", session.id)
    print("User ID:", session.user_id)

    return session.user
