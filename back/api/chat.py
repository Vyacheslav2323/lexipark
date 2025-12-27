from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from back.database.db import get_db
from back.database.models import Chat, Message, User
from back.core.auth import get_current_user
import uuid
from rq import Queue
from redis import Redis
from back.workers.analyze_message import analyze_message

redis = Redis(host="localhost", port=6379, db=0)
queue = Queue("mecab_analyzer", connection=redis)
router = APIRouter(prefix="/chat", tags=["chat"])

@router.get("")
def list_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.created_at.desc())
        .all()
    )
    return [
        {"id": str(c.id), "created_at": c.created_at}
        for c in chats
    ]
    
@router.post("/create")
def create_chat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = Chat(user_id=current_user.id)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return {"chat_id": chat.id}

class MessageCreate(BaseModel):
    chat_id: uuid.UUID
    role: str
    text: str

@router.post("/message")
def add_message(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == payload.chat_id).first()
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    msg = Message(
        chat_id=payload.chat_id,
        role=payload.role,
        text=payload.text
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    queue.enqueue(analyze_message, msg.id)
    return {"status": "ok", "message_id": msg.id}

@router.get("/{chat_id}")
def get_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at)
        .all()
    )

    return [
        {
            "id": m.id,
            "role": m.role,
            "text": m.text,
            "created_at": m.created_at
        }
        for m in messages
    ]