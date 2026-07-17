from fastapi import APIRouter

from app.common.deps import AuthServiceDep, CurrentUser
from app.common.envelope import Envelope, ok
from app.features.auth.schemas import LoginRequest, LoginResponse, UserDto

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest, service: AuthServiceDep) -> Envelope[LoginResponse]:
    access_token, user, organization = await service.authenticate(body.email, body.password)
    return ok(
        LoginResponse(access_token=access_token, user=UserDto.from_model(user, organization))
    )


@router.get("/me")
async def me(current_user: CurrentUser, service: AuthServiceDep) -> Envelope[UserDto]:
    organization = await service.get_organization_for(current_user)
    return ok(UserDto.from_model(current_user, organization))


@router.post("/logout")
async def logout(_: CurrentUser) -> Envelope[None]:
    return ok(None)
