"""Per-organization catalog/tips defaults, seeded at provisioning time.

Idempotent — every entity is matched on a natural key and inserted only when absent, so
re-running provisioning never duplicates rows. ``organization_id`` scoping columns land in a
later migration (B5); until then these defaults are shared across the whole table, which is
still safe to re-run because the natural-key match is unaffected by tenancy.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seeds import LENS_COATINGS, LENS_MATERIALS, LENS_TINTS, LENS_TYPES, TIPS
from app.db.seeds.support import existing_values
from app.db.seeds.types import LensOptionSeed
from app.features.lenses.models import LensCoating, LensMaterial, LensTint, LensType
from app.features.tips.models import Tip


async def _seed_lens_options(
    session: AsyncSession,
    model: type[LensType | LensMaterial | LensCoating | LensTint],
    seeds: tuple[LensOptionSeed, ...],
) -> None:
    existing = await existing_values(session, model.name_en)
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


async def seed_lens_catalog(session: AsyncSession) -> None:
    await _seed_lens_options(session, LensType, LENS_TYPES)
    await _seed_lens_options(session, LensMaterial, LENS_MATERIALS)
    await _seed_lens_options(session, LensCoating, LENS_COATINGS)
    await _seed_lens_options(session, LensTint, LENS_TINTS)


async def seed_tips(session: AsyncSession) -> None:
    existing = await existing_values(session, Tip.title_en)
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
