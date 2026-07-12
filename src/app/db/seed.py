"""Database seeding entrypoint.

Kept separate from migrations by design: migrations manage schema, this manages data.
Idempotent — every entity is matched on a natural key and inserted only when absent, so
re-running the script never duplicates rows.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.engine import get_sessionmaker
from app.db.seeds import (
    INVENTORY_ITEMS,
    LENS_COATINGS,
    LENS_MATERIALS,
    LENS_TINTS,
    LENS_TYPES,
    PATIENTS,
    TIPS,
)
from app.db.seeds.types import LensOptionSeed, PatientSeed
from app.features.auth.models import User, UserRole
from app.features.inventory.models import InventoryItem
from app.features.lenses.models import LensCoating, LensMaterial, LensTint, LensType
from app.features.patients.models import (
    LensConfig,
    Patient,
    PatientNote,
    VisitHistory,
)
from app.features.tips.models import Tip


async def _existing_values[ValueT](
    session: AsyncSession, column: InstrumentedAttribute[ValueT]
) -> set[ValueT]:
    result = await session.execute(select(column))
    return set(result.scalars().all())


async def _seed_lens_options(
    session: AsyncSession,
    model: type[LensType | LensMaterial | LensCoating | LensTint],
    seeds: tuple[LensOptionSeed, ...],
) -> None:
    existing = await _existing_values(session, model.name_en)
    for seed in seeds:
        if seed.name_en in existing:
            continue
        session.add(
            model(
                name_en=seed.name_en,
                name_ar=seed.name_ar,
                description_en=seed.description_en,
                description_ar=seed.description_ar,
                price=seed.price,
            )
        )


async def _seed_inventory(session: AsyncSession) -> None:
    existing = await _existing_values(session, InventoryItem.sku)
    for item in INVENTORY_ITEMS:
        if item.sku in existing:
            continue
        session.add(
            InventoryItem(
                category=item.category,
                name=item.name,
                brand=item.brand,
                spec=item.spec,
                shape=item.shape,
                color=item.color,
                sku=item.sku,
                qty=item.qty,
                threshold=item.threshold,
                price=item.price,
            )
        )


async def _seed_tips(session: AsyncSession) -> None:
    existing = await _existing_values(session, Tip.title_en)
    for tip in TIPS:
        if tip.title_en in existing:
            continue
        session.add(
            Tip(
                category=tip.category,
                tags=list(tip.tags),
                icon=tip.icon,
                color=tip.color,
                title_en=tip.title_en,
                title_ar=tip.title_ar,
                body_en=tip.body_en,
                body_ar=tip.body_ar,
            )
        )


def _build_patient(seed: PatientSeed) -> Patient:
    patient = Patient(
        name_en=seed.name_en,
        name_ar=seed.name_ar,
        phone=seed.phone,
        town_en=seed.town_en,
        town_ar=seed.town_ar,
        birth_year=seed.birth_year,
        last_visit=seed.last_visit,
        status=seed.status,
        rx_number=seed.rx_number,
        rx_date=seed.rx_date,
        od_sph=seed.od_sph,
        od_cyl=seed.od_cyl,
        od_axis=seed.od_axis,
        od_add=seed.od_add,
        os_sph=seed.os_sph,
        os_cyl=seed.os_cyl,
        os_axis=seed.os_axis,
        os_add=seed.os_add,
        pd_dist=seed.pd_dist,
        pd_near=seed.pd_near,
        diagnosis_en=seed.diagnosis_en,
        diagnosis_ar=seed.diagnosis_ar,
        tags=list(seed.tags),
        notes=[PatientNote(en=note.en, ar=note.ar) for note in seed.notes],
        visits=[
            VisitHistory(
                date=visit.date,
                title_en=visit.title_en,
                title_ar=visit.title_ar,
                detail_en=visit.detail_en,
                detail_ar=visit.detail_ar,
            )
            for visit in seed.visits
        ],
    )
    if seed.lens_config is not None:
        patient.lens_config = LensConfig(
            lens_type=seed.lens_config.lens_type,
            material=seed.lens_config.material,
            coatings=list(seed.lens_config.coatings),
            tint=seed.lens_config.tint,
            frame_sku=seed.lens_config.frame_sku,
        )
    return patient


async def _seed_patients(session: AsyncSession) -> None:
    existing = await _existing_values(session, Patient.rx_number)
    for seed in PATIENTS:
        if seed.rx_number in existing:
            continue
        session.add(_build_patient(seed))


async def _seed_doctor(session: AsyncSession, settings: Settings) -> None:
    if not settings.seed_doctor_email or not settings.seed_doctor_password:
        raise RuntimeError("SEED_DOCTOR_EMAIL and SEED_DOCTOR_PASSWORD must be configured")

    existing = await session.execute(
        select(User).where(User.email == settings.seed_doctor_email)
    )
    if existing.scalar_one_or_none() is not None:
        return

    session.add(
        User(
            email=settings.seed_doctor_email,
            hashed_password=hash_password(settings.seed_doctor_password),
            display_name_en=settings.seed_doctor_display_name_en or "Doctor",
            display_name_ar=settings.seed_doctor_display_name_ar or "طبيب",
            role=UserRole.OPTOMETRIST,
        )
    )


async def seed() -> None:
    settings = get_settings()
    async with get_sessionmaker()() as session, session.begin():
        await _seed_doctor(session, settings)
        await _seed_lens_options(session, LensType, LENS_TYPES)
        await _seed_lens_options(session, LensMaterial, LENS_MATERIALS)
        await _seed_lens_options(session, LensCoating, LENS_COATINGS)
        await _seed_lens_options(session, LensTint, LENS_TINTS)
        await _seed_inventory(session)
        await _seed_tips(session)
        await _seed_patients(session)


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
