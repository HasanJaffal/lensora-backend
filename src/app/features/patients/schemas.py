from datetime import date
from decimal import Decimal

from pydantic import Field

from app.common.schema import CamelModel
from app.features.patients.models import (
    LensConfig,
    Patient,
    PatientNote,
    PatientStatus,
    VisitHistory,
)


def _compute_age(birth_year: int) -> int:
    return date.today().year - birth_year


class RxSummaryDto(CamelModel):
    od_sph: Decimal | None
    os_sph: Decimal | None


class RefractionEyeDto(CamelModel):
    sph: Decimal | None = None
    cyl: Decimal | None = None
    axis: int | None = None
    add: Decimal | None = None


class RefractionDto(CamelModel):
    od: RefractionEyeDto
    os: RefractionEyeDto


class LensConfigDto(CamelModel):
    lens_type: str | None
    material: str | None
    coatings: list[str]
    tint: str | None
    frame_sku: str | None

    @classmethod
    def from_model(cls, config: LensConfig) -> "LensConfigDto":
        return cls(
            lens_type=config.lens_type,
            material=config.material,
            coatings=list(config.coatings),
            tint=config.tint,
            frame_sku=config.frame_sku,
        )


class PatientNoteDto(CamelModel):
    id: str
    en: str
    ar: str

    @classmethod
    def from_model(cls, note: PatientNote) -> "PatientNoteDto":
        return cls(id=str(note.id), en=note.en, ar=note.ar)


class VisitHistoryDto(CamelModel):
    id: str
    date: date
    title_en: str
    title_ar: str
    detail_en: str
    detail_ar: str

    @classmethod
    def from_model(cls, visit: VisitHistory) -> "VisitHistoryDto":
        return cls(
            id=str(visit.id),
            date=visit.date,
            title_en=visit.title_en,
            title_ar=visit.title_ar,
            detail_en=visit.detail_en,
            detail_ar=visit.detail_ar,
        )


class PatientListItemDto(CamelModel):
    id: str
    name_en: str
    name_ar: str
    phone: str
    age: int
    last_visit: date | None
    status: str
    rx_summary: RxSummaryDto

    @classmethod
    def from_model(cls, patient: Patient) -> "PatientListItemDto":
        return cls(
            id=str(patient.id),
            name_en=patient.name_en,
            name_ar=patient.name_ar,
            phone=patient.phone,
            age=_compute_age(patient.birth_year),
            last_visit=patient.last_visit,
            status=patient.status,
            rx_summary=RxSummaryDto(od_sph=patient.od_sph, os_sph=patient.os_sph),
        )


class PatientDto(CamelModel):
    id: str
    name_en: str
    name_ar: str
    phone: str
    town_en: str
    town_ar: str
    birth_year: int
    age: int
    last_visit: date | None
    status: str
    refraction: RefractionDto
    pd_dist: Decimal | None
    pd_near: Decimal | None
    diagnosis_en: str | None
    diagnosis_ar: str | None
    rx_number: str | None
    rx_date: date | None
    lens_config: LensConfigDto | None
    tags: list[str]
    notes: list[PatientNoteDto]
    history: list[VisitHistoryDto]

    @classmethod
    def from_model(cls, patient: Patient) -> "PatientDto":
        return cls(
            id=str(patient.id),
            name_en=patient.name_en,
            name_ar=patient.name_ar,
            phone=patient.phone,
            town_en=patient.town_en,
            town_ar=patient.town_ar,
            birth_year=patient.birth_year,
            age=_compute_age(patient.birth_year),
            last_visit=patient.last_visit,
            status=patient.status,
            refraction=RefractionDto(
                od=RefractionEyeDto(
                    sph=patient.od_sph,
                    cyl=patient.od_cyl,
                    axis=patient.od_axis,
                    add=patient.od_add,
                ),
                os=RefractionEyeDto(
                    sph=patient.os_sph,
                    cyl=patient.os_cyl,
                    axis=patient.os_axis,
                    add=patient.os_add,
                ),
            ),
            pd_dist=patient.pd_dist,
            pd_near=patient.pd_near,
            diagnosis_en=patient.diagnosis_en,
            diagnosis_ar=patient.diagnosis_ar,
            rx_number=patient.rx_number,
            rx_date=patient.rx_date,
            lens_config=(
                LensConfigDto.from_model(patient.lens_config)
                if patient.lens_config is not None
                else None
            ),
            tags=list(patient.tags),
            notes=[PatientNoteDto.from_model(note) for note in patient.notes],
            history=[VisitHistoryDto.from_model(visit) for visit in patient.visits],
        )


class NoteInput(CamelModel):
    en: str = Field(min_length=1)
    ar: str = Field(min_length=1)


class LensConfigInput(CamelModel):
    lens_type: str | None = None
    material: str | None = None
    coatings: list[str] = Field(default_factory=list)
    tint: str | None = None
    frame_sku: str | None = None


class PatientCreateRequest(CamelModel):
    name_en: str = Field(min_length=1)
    name_ar: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    town_en: str = Field(min_length=1)
    town_ar: str = Field(min_length=1)
    birth_year: int = Field(ge=1900, le=date.today().year)
    status: PatientStatus = PatientStatus.ACTIVE
    last_visit: date | None = None
    refraction: RefractionDto | None = None
    pd_dist: Decimal | None = None
    pd_near: Decimal | None = None
    diagnosis_en: str | None = None
    diagnosis_ar: str | None = None
    rx_number: str | None = None
    rx_date: date | None = None
    tags: list[str] = Field(default_factory=list)
    notes: list[NoteInput] = Field(default_factory=list)
    lens_config: LensConfigInput | None = None


class PatientUpdateRequest(CamelModel):
    name_en: str | None = Field(default=None, min_length=1)
    name_ar: str | None = Field(default=None, min_length=1)
    phone: str | None = Field(default=None, min_length=1)
    town_en: str | None = Field(default=None, min_length=1)
    town_ar: str | None = Field(default=None, min_length=1)
    birth_year: int | None = Field(default=None, ge=1900, le=date.today().year)
    status: PatientStatus | None = None
    last_visit: date | None = None
    refraction: RefractionDto | None = None
    pd_dist: Decimal | None = None
    pd_near: Decimal | None = None
    diagnosis_en: str | None = None
    diagnosis_ar: str | None = None
    rx_number: str | None = None
    rx_date: date | None = None
    tags: list[str] | None = None
    lens_config: LensConfigInput | None = None
