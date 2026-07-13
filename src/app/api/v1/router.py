from fastapi import APIRouter

from app.features.auth.router import router as auth_router
from app.features.inventory.router import router as inventory_router
from app.features.patients.router import router as patients_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(inventory_router)
