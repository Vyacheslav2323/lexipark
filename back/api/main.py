from typing import Union
from fastapi import FastAPI
from back.api.llm import router as llm_router
from fastapi.middleware.cors import CORSMiddleware
from back.api.chat import router as chat_router
from back.api.auth import router as auth_router
from back.api.mypage import router as mypage_router
from back.api.memorize import router as memorize_router
app = FastAPI()
app.include_router(chat_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(llm_router)
app.include_router(auth_router)
app.include_router(mypage_router)
app.include_router(memorize_router)
