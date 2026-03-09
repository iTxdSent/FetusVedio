import { apiGet, apiPost } from "@/api/http";

export interface Patient {
  id: number;
  name: string;
  patient_code: string;
  gestation_week: string;
  created_at: string;
}

export interface PatientCreatePayload {
  name: string;
  patient_code: string;
  gestation_week: string;
}

export function createPatient(payload: PatientCreatePayload): Promise<Patient> {
  return apiPost<Patient>("/patients/", payload);
}

export function listPatients(): Promise<Patient[]> {
  return apiGet<Patient[]>("/patients/");
}
