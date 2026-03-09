import { apiGet, apiPost, apiPostForm, resolveMediaUrl } from "@/api/http";

export type SourceMode = "capture" | "local";

export interface SessionState {
  exam_active: boolean;
  freeze: boolean;
  source_mode: SourceMode;
  source_state: string;
  local_video_path: string | null;
  frame_index: number;
  patient_id: number | null;
  session_id: number | null;
  auto_capture_status: string;
}

export interface StreamPayload {
  frame_index: number;
  image_base64: string;
  plane: string;
  confidence: number;
  metrics: Record<string, number>;
  metrics_px?: Record<string, number>;
  qc_pass: boolean;
  source_state: string;
  auto_capture_status: string;
  qc?: Record<string, boolean>;
  spacing_cm_per_pixel?: number | null;
}

export function getStreamState(): Promise<SessionState> {
  return apiGet<SessionState>("/stream/state");
}

export function startExam(patientId: number | null): Promise<SessionState> {
  return apiPost<SessionState>("/stream/start", patientId == null ? {} : { patient_id: patientId });
}

export function setSpacing(spacingCmPerPixel: number): Promise<SessionState> {
  return apiPost<SessionState>("/stream/spacing", { spacing_cm_per_pixel: spacingCmPerPixel });
}

export function endExam(): Promise<SessionState> {
  return apiPost<SessionState>("/stream/end");
}

export function freezeExam(): Promise<SessionState> {
  return apiPost<SessionState>("/stream/freeze");
}

export function unfreezeExam(): Promise<SessionState> {
  return apiPost<SessionState>("/stream/unfreeze");
}

export function switchLocalVideo(videoPath: string): Promise<SessionState> {
  return apiPost<SessionState>("/stream/switch-local-video", { video_path: videoPath });
}

export function resumeCapture(): Promise<SessionState> {
  return apiPost<SessionState>("/stream/resume-capture");
}

export function uploadLocalVideo(file: File): Promise<SessionState> {
  const formData = new FormData();
  formData.append("file", file);
  return apiPostForm<SessionState>("/stream/upload-local-video", formData);
}

export function manualSave(): Promise<{ snapshot_id: number; overlay_url: string; message: string }> {
  return apiPost<{ snapshot_id: number; overlay_url: string; message: string }>("/stream/manual-save").then((res) => ({
    ...res,
    overlay_url: resolveMediaUrl(res.overlay_url),
  }));
}
