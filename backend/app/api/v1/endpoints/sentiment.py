"""
Sentiment Analysis API Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api import deps
from app.services.sentiment_service import sentiment_service


router = APIRouter()


class SentimentAnalyzeRequest(BaseModel):
    text: str


@router.post("/analyze")
async def analyze_text(request: SentimentAnalyzeRequest):
    result = sentiment_service.analyze_text(request.text)
    return result


@router.post("/analyze-call/{call_id}")
async def analyze_call(
    call_id: int,
    db: Session = Depends(deps.get_db)
):
    result = sentiment_service.analyze_call_sentiment(db, call_id)
    return result


@router.get("/business")
async def get_business_sentiment(
    days: int = 30,
    business_id: int = Depends(deps.get_current_business_id),
    db: Session = Depends(deps.get_db)
):
    stats = sentiment_service.get_business_sentiment_stats(db, business_id, days)
    return stats


@router.post("/realtime")
async def analyze_realtime(request: SentimentAnalyzeRequest):
    result = sentiment_service.analyze_realtime(request.text)
    return result
