from pydantic import BaseModel
from datetime import datetime


class SignupRequest(BaseModel):

    username : str
    email : str
    password : str


class LoginRequest(BaseModel):

    email : str
    password : str



