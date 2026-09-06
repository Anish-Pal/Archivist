from sqlalchemy.orm import Session

from database.models import Conversation , Message , User



def create_conversation(
        db : Session,
        user_id : int,
        title : str
):

    conversation = Conversation(
        user_id = user_id,
        title = title
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation



def get_conversation(
        db : Session,
        conversation_id : int,
        user_id : int
):

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()

    return conversation



def save_message(
        db : Session,
        conversation_id : int,
        role : str,
        content : str,
        citations = None
):

    message = Message(
        conversation_id = conversation_id,
        role = role,
        content = content,
        citations = citations
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message




def get_messages(
        db : Session,
        conversation_id : int,
):

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).all()

    return messages




def get_message_history(
    db : Session,
    conversation_id : int
):

    messages = get_messages(
        db,
        conversation_id
    )

    history = []

    for message in messages:

        history.append({
            "role" : message.role,
            "content" : message.content
        })

    return history    



def update_conversation_title(
        db : Session,
        conversation_id : int,
        title : str
):

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if conversation:

        conversation.title = title[:50]
        db.commit()
        db.refresh(conversation)

    return conversation    



def get_user_conversations(
        db : Session,
        user_id : int,
):

    conversations = db.query(Conversation).join(Message).filter(
        Conversation.user_id == user_id
    ).all()

    return conversations



def get_user_by_email(
        db : Session,
        email : str
):
    return db.query(User).filter(
        User.email == email
    ).first()



def create_user(
        db : Session,
        username : str,
        email : str,
        password_hash : str
):
    user = User(
        username=username,
        email=email,
        password_hash=password_hash
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user