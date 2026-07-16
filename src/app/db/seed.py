"""Demo-data seeding entrypoint for local development.

Kept separate from migrations by design: migrations manage schema, this manages data.
Idempotent — every entity is matched on a natural key and inserted only when absent, so
re-running the script never duplicates rows. Accounts are provisioned separately via
``python -m app.management.provision_organization``; this script only seeds demo inventory
and patient records on top of whatever catalog/tips an organization already has.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_sessionmaker
from app.db.seeds import INVENTORY_ITEMS, PATIENTS
from app.db.seeds.organization_defaults import seed_lens_catalog, seed_tips
from app.db.seeds.support import existing_values
from app.db.seeds.types import PatientSeed
from app.features.inventory.models import InventoryItem
from app.features.patients.models import (
    LensConfig,
    Patient,
    PatientNote,
    VisitHistory,
)


async def _seed_inventory(session: AsyncSession) -> None:
    existing = await existing_values(session, InventoryItem.sku)
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
                quantity=item.quantity,
                threshold=item.threshold,
                price=item.price,
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
    existing = await existing_values(session, Patient.rx_number)
    for seed in PATIENTS:
        if seed.rx_number in existing:
            continue
        session.add(_build_patient(seed))


async def seed() -> None:
    async with get_sessionmaker()() as session, session.begin():
        await seed_lens_catalog(session)
        await seed_tips(session)
        await _seed_inventory(session)
        await _seed_patients(session)


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
