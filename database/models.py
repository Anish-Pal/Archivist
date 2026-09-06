from database.database import Base
from sqlalchemy import Column , Integer , String , ForeignKey ,DateTime , JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):

    __tablename__ = "users"

    id = Column(Integer , primary_key=True , index=True)

    username = Column(String , nullable=False)

    email = Column(String , unique=True , nullable=False)

    password_hash = Column(String , nullable=False)

    conversations = relationship(
        "Conversation",
        back_populates= "user"
    )

    sessions = relationship(
        "UserSession", 
        back_populates="user"
    )

    documents = relationship(
        "Documents",
        back_populates="user"
    )



class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(Integer , primary_key=True , index=True)

    user_id = Column(Integer , ForeignKey("users.id") , nullable=False)

    title = Column(String , nullable=True)

    user = relationship(
        "User",
        back_populates = "conversations"
    )

    messages = relationship(
        "Message",
        back_populates = "conversation"
    )



class Message(Base):

    __tablename__ = "messages"

    id = Column(Integer , primary_key=True , index=True)

    conversation_id = Column(Integer , ForeignKey("conversations.id") , nullable=False)

    role = Column(String , nullable=False)

    content = Column(String , nullable=False)

    citations = Column(JSON, nullable=True) 

    conversation = relationship(
        "Conversation",
        back_populates = "messages"
    )



class UserSession(Base):

    __tablename__ = "session"

    id = Column(Integer , primary_key=True , index=True)

    session_id = Column(String , unique=True , nullable=False , index=True)

    user_id = Column(Integer , ForeignKey("users.id") , nullable=False)

    expires_at = Column(DateTime , nullable=False)

    user = relationship(
        "User",
        back_populates="sessions"
    )



class Documents(Base):

    __tablename__ = "documents"

    id = Column(Integer , primary_key=True , index=True)

    user_id = Column(Integer , ForeignKey("users.id") , nullable=False)

    filename = Column(String, nullable=False)

    file_path = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship(
        "User",
        back_populates="documents"
    )




