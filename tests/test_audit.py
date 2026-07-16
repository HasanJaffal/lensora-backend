import uuid

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.features.auth.models import User
from app.features.inventory.models import InventoryItem
from app.features.patients.models import Patient


async def test_api_create_stamps_created_by_with_current_account(
    api_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    seeded_admin: User,
) -> None:
    payload = {
        "nameEn": "Audit Test Patient",
        "nameAr": "مريض اختبار التدقيق",
        "phone": "+961 70 000 111",
        "townEn": "Beirut",
        "townAr": "بيروت",
        "birthYear": 1995,
        "status": "active",
        "refraction": {
            "od": {"sph": None, "cyl": None, "axis": None, "add": None},
            "os": {"sph": None, "cyl": None, "axis": None, "add": None},
        },
        "tags": [],
        "notes": [],
    }

    created = await api_client.post("/api/v1/patients", json=payload)
    assert created.status_code == 200
    patient_id = uuid.UUID(created.json()["data"]["id"])

    async with db_sessionmaker() as session:
        result = await session.execute(select(Patient).where(Patient.id == patient_id))
        patient = result.scalar_one()

    assert patient.created_by == seeded_admin.id
    assert patient.updated_by == seeded_admin.id


async def test_api_update_stamps_updated_by_with_current_account(
    api_client: AsyncClient,
    db_sessionmaker: async_sessionmaker[AsyncSession],
    seeded_admin: User,
) -> None:
    async with db_sessionmaker() as session:
        result = await session.execute(select(InventoryItem).limit(1))
        item_id = result.scalar_one().id

    response = await api_client.patch(f"/api/v1/inventory/{item_id}", json={"qty": 3})
    assert response.status_code == 200

    async with db_sessionmaker() as session:
        result = await session.execute(select(InventoryItem).where(InventoryItem.id == item_id))
        item = result.scalar_one()

    assert item.updated_by == seeded_admin.id


async def test_seed_inserts_leave_actor_null(
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with db_sessionmaker() as session:
        result = await session.execute(select(Patient).limit(1))
        patient = result.scalar_one()

    assert patient.created_by is None
    assert patient.updated_by is None
