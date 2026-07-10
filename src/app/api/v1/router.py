from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Feature routers are registered here as they are implemented (patients, inventory, ...).
