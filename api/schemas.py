from typing import Optional
from pydantic import BaseModel
from typing import Union
from datetime import datetime


class ChatRequest(BaseModel):
    query : str
    conversation_id : int | None


class Source(BaseModel):
    number : int
    source : str
    page : Union[int , str]


class ChatResponse(BaseModel):
    conversation_id : int
    answer : str   
    title : str
    sources : list[Source]     


class Usercreate(BaseModel):
    name : str
    email : str


class ConversationsResponse(BaseModel):
    id : int
    title : str | None


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str   
    citations: Optional[list[Source]] = None

    class Config:
        from_attributes = True 


class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True



class DocumentResponse(BaseModel):

    id : int
    filename : str
    created_at : datetime

    class Config:
        from_attributes = True        