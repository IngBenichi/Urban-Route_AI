from fastapi import APIRouter, Request, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.auth import AIRecommendRequest, AIRecommendResponse
from app.services.ai_engine import get_ai_recommendation

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/recommend", response_model=AIRecommendResponse)
@limiter.limit("5/minute")
async def recommend(request: Request, body: AIRecommendRequest):
    try:
        answer = await get_ai_recommendation(query=body.query, context=body.context)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error al contactar el servicio de IA: {str(exc)}",
        )
    return AIRecommendResponse(answer=answer, query=body.query)
