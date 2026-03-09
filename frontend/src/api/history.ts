import { apiGet, resolveMediaUrl } from "@/api/http";

export interface SnapshotItem {
  id: number;
  patient_id: number;
  session_id: number;
  frame_index: number;
  plane: string;
  trigger_type: string;
  overlay_url: string;
  raw_url: string;
  result_json_url: string;
  created_at: string;
}

function normalize(item: SnapshotItem): SnapshotItem {
  return {
    ...item,
    overlay_url: resolveMediaUrl(item.overlay_url),
    raw_url: resolveMediaUrl(item.raw_url),
    result_json_url: resolveMediaUrl(item.result_json_url),
  };
}

export function listPatientSnapshots(patientId: number, limit = 200): Promise<SnapshotItem[]> {
  return apiGet<SnapshotItem[]>(`/history/patients/${patientId}/snapshots?limit=${limit}`).then((rows) =>
    rows.map(normalize),
  );
}

export function getLatestSnapshot(patientId: number): Promise<SnapshotItem | null> {
  return apiGet<SnapshotItem | null>(`/history/patients/${patientId}/latest-snapshot`).then((row) =>
    row ? normalize(row) : null,
  );
}
