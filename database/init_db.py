from database.database import Base, engine
# Imported so the tables register on Base.metadata before create_all.
from database.models import User, Conversation , Message  # noqa: F401


Base.metadata.create_all(bind=engine)
