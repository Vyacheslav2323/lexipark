from fastapi import APIRouter, Depends
from back.database.models import User, User_Vocab, User_Grammar, Vocab, Grammar
from back.database.db import get_db
from sqlalchemy.orm import Session
from back.core.auth import get_current_user
from back.logic.retention import recompute_recall

router = APIRouter(prefix="/mypage", tags=["mypage"])

@router.get("/vocab-table")
def get_vocab_table(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_vocabs = (
        db.query(User_Vocab)
        .filter(User_Vocab.user_id == current_user.id)
        .all()
    )
    for user_vocab in user_vocabs:
        recompute_recall(user_vocab)
    db.commit()
    rows = (
        db.query(
            Vocab.base.label("word"),
            Vocab.translation.label("translation"),
            User_Vocab.count.label("count"),
            User_Vocab.recall.label("recall"),
            User_Vocab.last_viewed.label("last_viewed"),
        )
        .join(User_Vocab, User_Vocab.vocab_id == Vocab.id)
        .filter(User_Vocab.user_id == current_user.id)
        .order_by(User_Vocab.count.desc(), User_Vocab.last_viewed.desc().nullslast())
        .all()
    )

    return [
        {
            "Word": r.word,
            "Translation": r.translation,
            "Count": r.count,
            "Recall": r.recall,
            "LastViewed": r.last_viewed,
        }
        for r in rows
    ]

@router.get("/grammar-table")
def get_grammar_table(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(
            Grammar.title,
            Grammar.function,
            Grammar.meaning,
            Grammar.boundary,
            User_Grammar.count,
            User_Grammar.recall
        )
        .join(User_Grammar, User_Grammar.grammar_id == Grammar.id)
        .filter(User_Grammar.user_id == current_user.id)
        .order_by(User_Grammar.count.desc())
        .all()
    )

    return [
        {
            "Grammar": row.title,
            "Function": row.function,
            "Meaning": row.meaning,
            "Boundary": row.boundary,
            "Count": row.count,
            "Recall": row.recall
        }
        for row in rows
    ]

@router.get("/vocab-chart")
def get_vocab_chart(current_user: User = Depends(get_current_user)):
    return {"message": "Hello, World!"}