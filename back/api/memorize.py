from fastapi import APIRouter, Depends
from back.database.models import User, User_Vocab, User_Grammar, Vocab, Grammar
from back.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from back.core.auth import get_current_user
from back.logic.retention import update_recall
from uuid import UUID
from pydantic import BaseModel

router = APIRouter(prefix="/memorize", tags=["memorize"])

@router.post("/get-cards")
def get_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    N = user.daily_limit

    total_count = (
        db.query(func.sum(User_Vocab.count))
        .filter(User_Vocab.user_id == current_user.id)
        .scalar()
    ) or 0

    if total_count == 0:
        return []

    score = (User_Vocab.count / total_count) * func.coalesce(1-User_Vocab.recall, 0.8)

    rows = (
        db.query(User_Vocab, Vocab)
        .join(Vocab, User_Vocab.vocab_id == Vocab.id)
        .filter(User_Vocab.user_id == current_user.id)
        .order_by(score.desc())
        .limit(N)
        .all()
    )

    # Return JSON the frontend can render
    return [
        {
            "vocab_id": uv.vocab_id,
            "base": v.base,
            "translation": v.translation,
            "recall": uv.recall,
            "count": uv.count,
        }
        for uv, v in rows
    ]

class ReviewRequest(BaseModel):
    vocab_id: UUID
    success: bool
    failures: int

@router.post("/review")
def review(
    payload: ReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uv = (
        db.query(User_Vocab)
        .filter(
            User_Vocab.user_id == current_user.id,
            User_Vocab.vocab_id == payload.vocab_id
        )
        .first()
    )

    if payload.success:
        update_recall(uv, payload.failures)

    db.commit()
    return {"status": "ok"}
