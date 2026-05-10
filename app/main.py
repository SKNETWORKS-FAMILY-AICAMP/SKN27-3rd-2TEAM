import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import CORS_ORIGINS
from app.core.logging_config import setup_logging
from app.core.middleware import LoggingMiddleware
from app.api.recommendation_routes import router as recommendation_router
from app.api.chatbot_routes import router as chatbot_router
from app.api.session_routes import router as session_router
from app.api.music_detail_routes import router as music_detail_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("RIMAS API starting up")
    yield
    logger.info("RIMAS API shutting down")


app = FastAPI(title="RIMAS API", version="4.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(recommendation_router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(chatbot_router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(session_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(music_detail_router, prefix="/api/music", tags=["music"])


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "RIMAS API v4"}
