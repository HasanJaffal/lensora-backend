from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.common.deps import SessionDep
from app.common.envelope import Envelope, ok
from app.features.organizations.repository import OrganizationRepository
from app.features.storefront.repository import StorefrontProductRepository
from app.features.storefront.schemas import PublicOrganizationDto, PublicProductDto
from app.features.storefront.service import StorefrontService, parse_public_category

# The only unauthenticated router in the app: customers browse a storefront without an
# account (FR-STORE-1), so there is deliberately no `require_auth` dependency here.
router = APIRouter(prefix="/storefront", tags=["storefront"])


def get_storefront_service(session: SessionDep) -> StorefrontService:
    return StorefrontService(OrganizationRepository(session), StorefrontProductRepository(session))


StorefrontServiceDep = Annotated[StorefrontService, Depends(get_storefront_service)]


@router.get("/{slug}")
async def get_storefront(
    slug: str, service: StorefrontServiceDep
) -> Envelope[PublicOrganizationDto]:
    return ok(await service.get_public_organization(slug))


@router.get("/{slug}/products")
async def list_storefront_products(
    slug: str,
    service: StorefrontServiceDep,
    category: Annotated[str | None, Query()] = None,
) -> Envelope[list[PublicProductDto]]:
    return ok(await service.list_public_products(slug, parse_public_category(category)))
