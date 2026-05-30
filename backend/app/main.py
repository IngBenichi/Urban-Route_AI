from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers import auth_router, routes_router, stops_router, search_router, ai_router

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Urban Route AI",
    description="API del Sistema Inteligente de Rutas de Buses de Barranquilla",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api")
app.include_router(routes_router, prefix="/api")
app.include_router(stops_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(ai_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "urban-route-ai"}
