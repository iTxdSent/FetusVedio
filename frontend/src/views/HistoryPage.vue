<template>
  <section class="panel history-panel">
    <header class="panel-head">
      <p class="panel-tag">数据回溯</p>
      <h2>历史记录查询</h2>
      <p class="panel-desc">支持按患者 ID 查询并预览该患者所有留图记录。</p>
    </header>

    <div class="history-query-row">
      <label class="field">
        <span>患者ID</span>
        <input v-model.number="patientId" class="input-control" type="number" min="1" placeholder="请输入患者ID" />
      </label>
      <button class="btn btn-primary" :disabled="loading" @click="queryHistory">查询</button>
    </div>

    <p class="status-text">{{ message }}</p>

    <div v-if="records.length > 0" class="history-list">
      <article v-for="row in records" :key="row.id" class="history-item">
        <div class="history-head">
          <strong>#{{ row.id }}</strong>
          <span>{{ row.plane }}</span>
          <span>{{ row.trigger_type === "auto" ? "自动" : "手动" }}</span>
          <span>{{ formatTime(row.created_at) }}</span>
        </div>
        <img :src="row.overlay_url" alt="留图" class="history-img" />
      </article>
    </div>
    <p v-else class="muted">暂无查询结果</p>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { listPatientSnapshots, type SnapshotItem } from "@/api/history";

const loading = ref(false);
const message = ref("请输入患者ID后查询");
const patientId = ref<number | null>(null);
const records = ref<SnapshotItem[]>([]);

function loadStoredPatientId() {
  const raw = localStorage.getItem("fetus_demo_patient");
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw) as { id?: number };
    if (typeof parsed.id === "number") {
      patientId.value = parsed.id;
    }
  } catch {
    // ignore
  }
}

async function queryHistory() {
  if (!patientId.value) {
    message.value = "请先输入有效的患者ID";
    return;
  }

  loading.value = true;
  try {
    records.value = await listPatientSnapshots(patientId.value, 200);
    message.value = `查询完成，共 ${records.value.length} 条留图记录`;
  } catch (error) {
    message.value = error instanceof Error ? error.message : "查询失败";
  } finally {
    loading.value = false;
  }
}

function formatTime(text: string) {
  return new Date(text).toLocaleString("zh-CN", { hour12: false });
}

onMounted(async () => {
  loadStoredPatientId();
  if (patientId.value) {
    await queryHistory();
  }
});
</script>
