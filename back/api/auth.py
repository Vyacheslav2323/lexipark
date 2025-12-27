from fastapi import APIRouter, Header, HTTPException, Depends
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session

from back.database.db import get_db
from back.database.models import User
from back.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = "614213081580-9heabahooqahutmdlc1t5ol26a64ngev.apps.googleusercontent.com"


@router.post("/google")
def google_login(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.replace("Bearer ", "")

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = idinfo.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Email not found")

    # 1. resolve or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. issue app JWT
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email
    })

    return {
        "access_token": access_token
    }
