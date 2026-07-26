from fastapi import APIRouter

from app.features.ai.router import router as ai_router
from app.features.attachments.router import router as attachments_router
from app.features.auth.router import router as auth_router
from app.features.dashboard.router import router as dashboard_router
from app.features.import_forms.router import router as imports_router
from app.features.intake.router import router as intake_router
from app.features.inventory.router import router as inventory_router
from app.features.lenses.router import router as lenses_router
from app.features.patients.router import router as patients_router
from app.features.platform_admin.router import router as platform_admin_router
from app.features.storefront.router import router as storefront_router
from app.features.tips.router import router as tips_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(platform_admin_router)
api_router.include_router(inventory_router)
api_router.include_router(lenses_router)
api_router.include_router(tips_router)
api_router.include_router(intake_router)
api_router.include_router(ai_router)
api_router.include_router(imports_router)
api_router.include_router(dashboard_router)
api_router.include_router(storefront_router)
api_router.include_router(attachments_router)
