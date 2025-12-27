from fastapi import APIRouter
from pydantic import BaseModel
from back.logic.llm import translate, lesson
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/llm", tags=["llm"])

class TranslateInput(BaseModel):
    text: str

class LessonInput(BaseModel):
    grammar_vocab: str
    sentence: str

@router.post("/translate")
async def translate_endpoint(payload: TranslateInput):
    return await run_in_threadpool(translate, payload.text)

@router.post("/lesson")
async def lesson_endpoint(payload: LessonInput):
    return await run_in_threadpool(lesson, payload.grammar_vocab, payload.sentence)

