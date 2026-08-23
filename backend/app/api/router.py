from fastapi import APIRouter

from app.modules.analysis.router import router as analysis_router
from app.modules.auth.router import router as auth_router
from app.modules.chat_router import router as chat_router
from app.modules.documents.router import router as documents_router
from app.modules.interview_router import router as interview_router
from app.modules.roadmap.router import router as roadmap_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(roadmap_router, prefix="/roadmap", tags=["roadmap"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(interview_router, prefix="/interview", tags=["interview"])
