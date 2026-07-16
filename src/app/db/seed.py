"""Demo-data seeding entrypoint for local development.

Kept separate from migrations by design: migrations manage schema, this manages data.
Idempotent per organization — every entity is matched on a natural key scoped to that
org, so re-running the script never duplicates rows. Accounts are provisioned separately
via ``python -m app.management.provision_organization``; this script only seeds demo
inventory and patient records on top of whatever catalog/tips an organization already has.
"""

import argparse
import asyncio
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AppError, NotFoundError
from app.db.engine import get_sessionmaker
from app.db.seeds import INVENTORY_ITEMS, PATIENTS
from app.db.seeds.organization_defaults import seed_lens_catalog, seed_tips
from app.db.seeds.support import existing_values_for_org
from app.db.seeds.types import PatientSeed
from app.features.inventory.models import InventoryItem
from app.features.organizations.repository import OrganizationRepository
from app.features.patients.models import (
    LensConfig,
    Patient,
    PatientNote,
    VisitHistory,
)


async def _seed_inventory(session: AsyncSession, organization_id: uuid.UUID) -> None:
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


async def _seed_patients(session: AsyncSession, organization_id: uuid.UUID) -> None:
    existing = await existing_values_for_org(session, Patient, Patient.rx_number, organization_id)
    for seed in PATIENTS:
        if seed.rx_number in existing:
            continue
        session.add(_build_patient(seed, organization_id))


async def seed(organization_slug: str) -> None:
    async with get_sessionmaker()() as session, session.begin():
        organization = await OrganizationRepository(session).get_by_slug(organization_slug)
        if organization is None:
            raise NotFoundError(f"Organization slug '{organization_slug}' not found")
        organization_id = organization.id
        await seed_lens_catalog(session, organization_id)
        await seed_tips(session, organization_id)
        await _seed_inventory(session, organization_id)
        await _seed_patients(session, organization_id)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed demo catalog/tips/inventory/patient data for one organization."
    )
    parser.add_argument(
        "--org-slug", required=True, help="Slug of an already-provisioned organization"
    )
    args = parser.parse_args()
    try:
        asyncio.run(seed(args.org_slug))
    except AppError as error:
        print(f"Seeding failed: {error.message}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
