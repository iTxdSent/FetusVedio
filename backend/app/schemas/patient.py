from datetime import datetime

from pydantic import BaseModel


class PatientCreateRequest(BaseModel):
    name: str
    patient_code: str
    gestation_week: str


class PatientResponse(BaseModel):
    id: int
    name: str
    patient_code: str
    gestation_week: str
    created_at: datetime
