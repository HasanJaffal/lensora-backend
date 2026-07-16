import uuid

from app.common.exceptions import PatientNotFoundError
from app.common.pagination import PaginationMeta
from app.common.tenant_context import TenantContext
from app.features.patients.models import (
    LensConfig,
    Patient,
    PatientNote,
    PatientStatus,
)
from app.features.patients.repository import PatientRepository
from app.features.patients.schemas import (
    LensConfigInput,
    PatientCreateRequest,
    PatientDto,
    PatientListItemDto,
    PatientUpdateRequest,
    RefractionDto,
    VisitHistoryDto,
)


class PatientService:
    """Business logic for patient records: listing, search, and record maintenance."""

    def __init__(self, patients: PatientRepository, tenant_context: TenantContext) -> None:
        self._patients = patients
        self._tenant_context = tenant_context

    async def list_patients(
        self,
        *,
        status: PatientStatus | None,
        query: str | None,
        page: int,
        page_size: int,
        offset: int,
    ) -> tuple[list[PatientListItemDto], PaginationMeta]:
        records, total = await self._patients.list_page(
            status=status, query=query, offset=offset, limit=page_size
        )
        items = [PatientListItemDto.from_model(record) for record in records]
        meta = PaginationMeta.build(page=page, page_size=page_size, total=total)
        return items, meta

    async def get_patient(self, patient_id: uuid.UUID) -> PatientDto:
        patient = await self._require_patient(patient_id)
        return PatientDto.from_model(patient)

    async def get_history(self, patient_id: uuid.UUID) -> list[VisitHistoryDto]:
        patient = await self._require_patient(patient_id)
        return [VisitHistoryDto.from_model(visit) for visit in patient.visits]

    async def create_patient(self, request: PatientCreateRequest) -> PatientDto:
        organization_id = self._tenant_context.organization_id
        patient = Patient(
            organization_id=organization_id,
            name_en=request.name_en,
            name_ar=request.name_ar,
            phone=request.phone,
            town_en=request.town_en,
            town_ar=request.town_ar,
            birth_year=request.birth_year,
            status=request.status.value,
            last_visit=request.last_visit,
            pd_dist=request.pd_dist,
            pd_near=request.pd_near,
            diagnosis_en=request.diagnosis_en,
            diagnosis_ar=request.diagnosis_ar,
            rx_number=request.rx_number,
            rx_date=request.rx_date,
            tags=list(request.tags),
            notes=[
                PatientNote(organization_id=organization_id, en=note.en, ar=note.ar)
                for note in request.notes
            ],
        )
        if request.refraction is not None:
            _assign_refraction(patient, request.refraction)
        if request.lens_config is not None:
            patient.lens_config = _build_lens_config(request.lens_config, organization_id)

        self._patients.add(patient)
        await self._patients.commit()
        await self._patients.refresh(patient)
        return PatientDto.from_model(patient)

    async def update_patient(
        self, patient_id: uuid.UUID, request: PatientUpdateRequest
    ) -> PatientDto:
        patient = await self._require_patient(patient_id)
        changed = request.model_fields_set

        for field in (
            "name_en",
            "name_ar",
            "phone",
            "town_en",
            "town_ar",
            "birth_year",
            "last_visit",
            "pd_dist",
            "pd_near",
            "diagnosis_en",
            "diagnosis_ar",
            "rx_number",
            "rx_date",
        ):
            if field in changed:
                setattr(patient, field, getattr(request, field))

        if "status" in changed and request.status is not None:
            patient.status = request.status.value
        if "tags" in changed and request.tags is not None:
            patient.tags = list(request.tags)
        if "refraction" in changed and request.refraction is not None:
            _assign_refraction(patient, request.refraction)
        if "lens_config" in changed:
            _apply_lens_config(patient, request.lens_config, patient.organization_id)

        await self._patients.commit()
        await self._patients.refresh(patient)
        return PatientDto.from_model(patient)

    async def _require_patient(self, patient_id: uuid.UUID) -> Patient:
        patient = await self._patients.get_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"Patient {patient_id} not found")
        return patient


def _assign_refraction(patient: Patient, refraction: RefractionDto) -> None:
    patient.od_sph = refraction.od.sph
    patient.od_cyl = refraction.od.cyl
    patient.od_axis = refraction.od.axis
    patient.od_add = refraction.od.add
    patient.os_sph = refraction.os.sph
    patient.os_cyl = refraction.os.cyl
    patient.os_axis = refraction.os.axis
    patient.os_add = refraction.os.add


def _build_lens_config(config: LensConfigInput, organization_id: uuid.UUID) -> LensConfig:
    return LensConfig(
        organization_id=organization_id,
        lens_type=config.lens_type,
        material=config.material,
        coatings=list(config.coatings),
        tint=config.tint,
        frame_sku=config.frame_sku,
    )


def _apply_lens_config(
    patient: Patient, config: LensConfigInput | None, organization_id: uuid.UUID
) -> None:
    if config is None:
        patient.lens_config = None
        return
    if patient.lens_config is None:
        patient.lens_config = _build_lens_config(config, organization_id)
        return
    patient.lens_config.lens_type = config.lens_type
    patient.lens_config.material = config.material
    patient.lens_config.coatings = list(config.coatings)
    patient.lens_config.tint = config.tint
    patient.lens_config.frame_sku = config.frame_sku
