from database.database import Base, engine
from database.models import User, Conversation , Message


Base.metadata.create_all(bind=engine)