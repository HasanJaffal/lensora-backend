"""Deterministic inventory/patient rows used to populate a tenant for tests.

Test-only by design: the application never ships demo data, so an organization provisioned
in production starts with nothing but its catalog/tips defaults.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seeds.support import existing_values_for_org
from app.features.inventory.models import InventoryItem
from app.features.patients.models import (
    LensConfig,
    Patient,
    PatientNote,
    VisitHistory,
)
from tests.fixtures.inventory import INVENTORY_ITEMS
from tests.fixtures.patients import PATIENTS
from tests.fixtures.types import PatientSeed


def _build_patient(seed: PatientSeed, organization_id: uuid.UUID) -> Patient:
    patient = Patient(
        organization_id=organization_id,
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
        notes=[
            PatientNote(organization_id=organization_id, en=note.en, ar=note.ar)
            for note in seed.notes
        ],
        visits=[
            VisitHistory(
                organization_id=organization_id,
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
            organization_id=organization_id,
            lens_type=seed.lens_config.lens_type,
            material=seed.lens_config.material,
            coatings=list(seed.lens_config.coatings),
            tint=seed.lens_config.tint,
            frame_sku=seed.lens_config.frame_sku,
        )
    return patient


async def insert_inventory_fixture(session: AsyncSession, organization_id: uuid.UUID) -> None:
    existing = await existing_values_for_org(
        session, InventoryItem, InventoryItem.sku, organization_id
    )
    for item in INVENTORY_ITEMS:
        if item.sku in existing:
            continue
        session.add(
            InventoryItem(
                organization_id=organization_id,
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


async def insert_patient_fixture(session: AsyncSession, organization_id: uuid.UUID) -> None:
    existing = await existing_values_for_org(session, Patient, Patient.rx_number, organization_id)
    for seed in PATIENTS:
        if seed.rx_number in existing:
            continue
        session.add(_build_patient(seed, organization_id))
