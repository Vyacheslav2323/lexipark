from sqlalchemy import Column, Text, ForeignKey, DateTime, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid, datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    daily_limit = Column(Integer, default=10)

class Chat(Base):
    __tablename__ = "chats"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID, ForeignKey("chats.id"))
    role = Column(Text)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Vocab(Base):
    __tablename__ = "vocabs"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    base = Column(Text)
    pos = Column(Text)
    translation = Column(Text)
    message_id = Column(UUID, ForeignKey("messages.id"))
    count = Column(Integer)

class User_Vocab(Base):
    __tablename__ = "user_vocabs"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    vocab_id = Column(UUID, ForeignKey("vocabs.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    count = Column(Integer)
    recall = Column(Float)
    last_viewed = Column(DateTime)
    learning_inertia = Column(Float)

class Grammar(Base):
    __tablename__ = "grammars"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    function = Column(Text)
    form = Column(Text)
    meaning = Column(Text)
    example = Column(Text)
    boundary = Column(Text)
    mistakes = Column(Text)
    count = Column(Integer)
    message_id = Column(UUID, ForeignKey("messages.id"))

class User_Grammar(Base):
    __tablename__ = "user_grammars"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    grammar_id = Column(UUID, ForeignKey("grammars.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    count = Column(Integer)
    recall = Column(Float)
    last_viewed = Column(DateTime)

class VocabOccurrence(Base):
    __tablename__ = "vocab_occurrences"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    vocab_id = Column(UUID, ForeignKey("vocabs.id"))
    message_id = Column(UUID, ForeignKey("messages.id"))

class GrammarOccurrence(Base):
    __tablename__ = "grammar_occurrences"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    grammar_id = Column(UUID, ForeignKey("grammars.id"))
    message_id = Column(UUID, ForeignKey("messages.id"))