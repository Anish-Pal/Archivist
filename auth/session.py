import secrets
from datetime import datetime , timedelta

from sqlalchemy.orm import Session

from database.models import UserSession


def create_session(
        db : Session,
        user_id : int
):

    session_id = secrets.token_urlsafe(32)

    expires_at = datetime.utcnow() + timedelta(days=1)

    new_session = UserSession(
        session_id = session_id,
        user_id = user_id,
        expires_at = expires_at
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session

