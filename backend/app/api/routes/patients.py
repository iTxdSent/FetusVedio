from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.schemas.patient import PatientCreateRequest, PatientResponse
from app.services.auth_service import AuthUser
from app.services.persistence import PersistenceService

router = APIRouter()
service = PersistenceService()


@router.get("/", response_model=list[PatientResponse])
def list_patients(current_user: AuthUser = Depends(get_current_user)) -> list[PatientResponse]:
    rows = service.list_patients(user_id=current_user.id)
    return [
        PatientResponse(
            id=row.id,
            name=row.name,
            patient_code=row.patient_code,
            gestation_week=row.gestation_week,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/", response_model=PatientResponse)
def create_patient(payload: PatientCreateRequest, current_user: AuthUser = Depends(get_current_user)) -> PatientResponse:
    row = service.create_patient(
        user_id=current_user.id,
        name=payload.name,
        patient_code=payload.patient_code,
        gestation_week=payload.gestation_week,
    )
    return PatientResponse(
        id=row.id,
        name=row.name,
        patient_code=row.patient_code,
        gestation_week=row.gestation_week,
        created_at=row.created_at,
    )
