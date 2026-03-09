<template>
  <section class="realtime-shell">
    <div class="panel video-panel">
      <header class="panel-head compact">
        <h2>超声影像</h2>
        <p class="panel-desc"></p>
      </header>

      <div class="video-frame">
        <img v-if="frameUrl" :src="frameUrl" alt="实时视频帧" />
        <div v-else class="video-placeholder">等待视频流...</div>
      </div>

      <div class="source-line">
        <span>视频源</span>
        <strong>{{ videoSourceText }}</strong>
      </div>

      <div class="btn-grid">
        <button class="btn btn-primary" :disabled="busy || !canStart" @click="handleStart">开始检查</button>
        <button class="btn btn-secondary" :disabled="busy" @click="handleEnd">结束检查</button>
        <button class="btn btn-secondary" :disabled="busy || !streamState?.exam_active" @click="handleToggleFreeze">
          {{ freezeToggleText }}
        </button>
        <button class="btn btn-secondary" :disabled="busy || !streamState?.exam_active" @click="handleManualSave">留图</button>
        <button class="btn btn-secondary" :disabled="busy" @click="handleSwitchLocal">选择本地视频</button>
        <button class="btn btn-secondary" :disabled="busy || !canResumeCapture" @click="handleResumeCapture">恢复视频流</button>
      </div>
      <input
        ref="fileInputRef"
        class="hidden-file-input"
        type="file"
        accept="video/*,.avi,.mp4,.mov,.mkv,.m4v"
        @change="handleLocalFileChange"
      />

      <p class="status-text">状态：{{ opMessage }}</p>
    </div>

    <aside class="panel result-panel">
      <header class="panel-head compact">
        <h2>结果信息</h2>
        <p class="panel-desc"></p>
      </header>

      <section class="info-group">
        <h3>比例尺设置</h3>
        <div class="spacing-row">
          <input
            v-model="spacingInput"
            class="input-control"
            type="number"
            step="0.0001"
            min="0"
            placeholder="请输入比例尺（cm/px）"
          />
          <button class="btn btn-primary" :disabled="busy" @click="handleConfirmSpacing">确定</button>
        </div>
        <p class="inline-metric"><span>当前比例尺</span><strong>{{ spacingText }}</strong></p>
        <p class="inline-metric">
          <span>状态</span>
          <strong>{{ streamState?.spacing_confirmed ? "已确认" : "未确认（禁止开始检查）" }}</strong>
        </p>
      </section>

      <section class="info-group">
        <h3>切面识别</h3>
        <p class="inline-metric"><span>当前切面</span><strong>{{ payload?.plane ?? "--" }}</strong></p>
        <p class="inline-metric"><span>分类置信度</span><strong>{{ confidenceText }}</strong></p>
        <p class="inline-metric">
          <span>自动留图状态</span>
          <strong>{{ payload?.auto_capture_status ?? streamState?.auto_capture_status ?? "--" }}</strong>
        </p>
      </section>

      <section class="info-group">
        <h3>测量值（mm）</h3>
        <ul class="metric-list-fixed">
          <li v-for="(item, idx) in fixedMetricRows" :key="`metric-${idx}`" class="metric-row">
            <template v-if="item">
              <span>{{ item[0] }}</span>
              <strong>{{ item[1].toFixed(2) }} mm</strong>
            </template>
            <template v-else>
              <span>&nbsp;</span>
              <strong>&nbsp;</strong>
            </template>
          </li>
        </ul>
      </section>

      <section class="info-group">
        <h3>留图预览</h3>
        <div class="preview-box">
          <img v-if="previewUrl" :src="previewUrl" alt="留图预览" />
          <p v-else class="muted">当前患者暂无留图</p>
        </div>
        <div class="preview-actions">
          <button class="btn btn-secondary" :disabled="busy || snapshotOptions.length === 0" @click="showPicker = !showPicker">
            选择留存图片
          </button>
          <button class="btn btn-secondary" :disabled="busy || !patientId" @click="refreshSnapshots">刷新留图列表</button>
        </div>
        <div v-if="showPicker" class="picker-row">
          <select v-model="selectedSnapshotId" class="input-control" @change="applySelectedSnapshot">
            <option disabled value="">请选择留图记录</option>
            <option v-for="snap in snapshotOptions" :key="snap.id" :value="String(snap.id)">
              #{{ snap.id }} {{ snap.plane }} {{ snap.trigger_type }} {{ formatTime(snap.created_at) }}
            </option>
          </select>
        </div>
      </section>

      <section class="info-group">
        <h3>会话状态</h3>
        <p class="inline-metric"><span>当前用户</span><strong>{{ currentUsername }}</strong></p>
        <p class="inline-metric"><span>患者ID</span><strong>{{ streamState?.patient_id ?? "--" }}</strong></p>
        <p class="inline-metric"><span>检查中</span><strong>{{ streamState?.exam_active ? "是" : "否" }}</strong></p>
      </section>
    </aside>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

import { getLatestSnapshot, listPatientSnapshots, type SnapshotItem } from "@/api/history";
import { getUser } from "@/auth/session";
import {
  type SessionState,
  type StreamPayload,
  endExam,
  freezeExam,
  getStreamState,
  manualSave,
  resumeCapture,
  setSpacing,
  startExam,
  unfreezeExam,
  uploadLocalVideo,
} from "@/api/stream";
import { createStreamSocket } from "@/api/ws";

const busy = ref(false);
const opMessage = ref("就绪");
const payload = ref<StreamPayload | null>(null);
const streamState = ref<SessionState | null>(null);
const wsRef = ref<WebSocket | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

const spacingInput = ref("");
const showPicker = ref(false);
const selectedSnapshotId = ref("");
const snapshotOptions = ref<SnapshotItem[]>([]);
const previewUrl = ref("");

let pollTimer: number | undefined;

const patientId = computed(() => streamState.value?.patient_id ?? getStoredPatientId());
const canStart = computed(() => Boolean(streamState.value?.spacing_confirmed && patientId.value));
const canResumeCapture = computed(() => streamState.value?.source_mode === "local");
const spacingText = computed(() => {
  const val = streamState.value?.spacing_cm_per_pixel;
  if (val == null) return "--";
  return `${val.toFixed(4)} cm/px`;
});
const currentUsername = computed(() => getUser()?.username ?? "--");
const freezeToggleText = computed(() => (streamState.value?.freeze ? "解冻" : "冻结"));
const videoSourceText = computed(() => {
  const mode = streamState.value?.source_mode;
  if (mode === "local") return "本地视频";
  if (mode === "capture") return "采集卡";
  return payload.value?.source_state ?? streamState.value?.source_state ?? "--";
});

const frameUrl = computed(() => {
  if (!payload.value?.image_base64) return "";
  return `data:image/jpeg;base64,${payload.value.image_base64}`;
});

const fixedMetricRows = computed(() => {
  const entries = Object.entries(payload.value?.metrics ?? {});
  return Array.from({ length: 4 }, (_, idx) => entries[idx] ?? null);
});

const confidenceText = computed(() => {
  if (payload.value == null) return "--";
  return `${(payload.value.confidence * 100).toFixed(1)}%`;
});

function getStoredPatientId(): number | null {
  const raw = localStorage.getItem("fetus_demo_patient");
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { id?: number };
    return typeof parsed.id === "number" ? parsed.id : null;
  } catch {
    return null;
  }
}

async function refreshState() {
  streamState.value = await getStreamState();
  if (streamState.value?.spacing_cm_per_pixel != null && spacingInput.value === "") {
    spacingInput.value = String(streamState.value.spacing_cm_per_pixel);
  }
}

async function refreshSnapshots() {
  if (!patientId.value) return;
  snapshotOptions.value = await listPatientSnapshots(patientId.value, 200);
  const latest = await getLatestSnapshot(patientId.value);
  if (latest) {
    previewUrl.value = latest.overlay_url;
    selectedSnapshotId.value = String(latest.id);
  }
}

function applySelectedSnapshot() {
  const target = snapshotOptions.value.find((item) => String(item.id) === selectedSnapshotId.value);
  if (target) {
    previewUrl.value = target.overlay_url;
  }
}

function connectWs() {
  wsRef.value?.close();
  wsRef.value = createStreamSocket({
    onOpen: () => {},
    onClose: () => {},
    onError: () => {},
    onMessage: (data) => {
      if (typeof data === "object" && data !== null) {
        payload.value = data as StreamPayload;
      }
    },
  });
}

async function doAction(fn: () => Promise<SessionState>, successText: string) {
  busy.value = true;
  try {
    streamState.value = await fn();
    opMessage.value = successText;
  } catch (error) {
    opMessage.value = error instanceof Error ? error.message : "操作失败";
  } finally {
    busy.value = false;
  }
}

function handleStart() {
  if (!canStart.value) {
    opMessage.value = "请先确认比例尺并确保已选择患者";
    return;
  }
  void doAction(() => startExam(getStoredPatientId()), "已开始检查");
}

function handleEnd() {
  void doAction(endExam, "已结束检查");
}

function handleToggleFreeze() {
  if (streamState.value?.freeze) {
    void doAction(unfreezeExam, "已解冻");
    return;
  }
  void doAction(freezeExam, "已冻结");
}

function handleResumeCapture() {
  void doAction(resumeCapture, "已恢复采集卡视频流");
}

function handleSwitchLocal() {
  fileInputRef.value?.click();
}

async function handleLocalFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  await doAction(() => uploadLocalVideo(file), `已上传并切换本地视频：${file.name}`);
  input.value = "";
}

async function handleManualSave() {
  busy.value = true;
  try {
    const res = await manualSave();
    previewUrl.value = res.overlay_url;
    opMessage.value = res.message;
    await refreshSnapshots();
  } catch (error) {
    opMessage.value = error instanceof Error ? error.message : "留图失败";
  } finally {
    busy.value = false;
  }
}

async function handleConfirmSpacing() {
  const spacing = Number(spacingInput.value);
  if (!Number.isFinite(spacing) || spacing <= 0) {
    opMessage.value = "请输入有效的比例尺（cm/px）";
    return;
  }
  await doAction(() => setSpacing(spacing), `比例尺已确认：${spacing.toFixed(4)} cm/px`);
}

function formatTime(text: string) {
  return new Date(text).toLocaleString("zh-CN", { hour12: false });
}

onMounted(async () => {
  try {
    await refreshState();
    await refreshSnapshots();
  } catch (error) {
    opMessage.value = error instanceof Error ? error.message : "初始化失败";
  }
  connectWs();
  pollTimer = window.setInterval(() => {
    void refreshState().catch(() => {});
    void refreshSnapshots().catch(() => {
      // ignore periodic history refresh error
    });
  }, 3000);
});

onUnmounted(() => {
  if (pollTimer) {
    window.clearInterval(pollTimer);
  }
  wsRef.value?.close();
});
</script>
