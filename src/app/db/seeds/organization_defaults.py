"""Per-organization catalog/tips defaults, seeded at provisioning time.

Idempotent per organization — every entity is matched on a natural key scoped to
``organization_id``, so re-running provisioning for the same org never duplicates rows.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seeds import LENS_COATINGS, LENS_MATERIALS, LENS_TINTS, LENS_TYPES, TIPS
from app.db.seeds.support import existing_values_for_org
from app.db.seeds.types import LensOptionSeed
from app.features.lenses.models import LensCoating, LensMaterial, LensTint, LensType
from app.features.tips.models import Tip


async def _seed_lens_options(
    session: AsyncSession,
    model: type[LensType | LensMaterial | LensCoating | LensTint],
    seeds: tuple[LensOptionSeed, ...],
    organization_id: uuid.UUID,
) -> None:
    existing = await existing_values_for_org(session, model, model.name_en, organization_id)
    for seed in seeds:
        if seed.name_en in existing:
            continue
        session.add(
            model(
                organization_id=organization_id,
                name_en=seed.name_en,
                name_ar=seed.name_ar,
                description_en=seed.description_en,
                description_ar=seed.description_ar,
                price=seed.price,
            )
        )


async def seed_lens_catalog(session: AsyncSession, organization_id: uuid.UUID) -> None:
    await _seed_lens_options(session, LensType, LENS_TYPES, organization_id)
    await _seed_lens_options(session, LensMaterial, LENS_MATERIALS, organization_id)
    await _seed_lens_options(session, LensCoating, LENS_COATINGS, organization_id)
    await _seed_lens_options(session, LensTint, LENS_TINTS, organization_id)


async def seed_tips(session: AsyncSession, organization_id: uuid.UUID) -> None:
    existing = await existing_values_for_org(session, Tip, Tip.title_en, organization_id)
    for tip in TIPS:
        if tip.title_en in existing:
            continue
        session.add(
            Tip(
                organization_id=organization_id,
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
