<template>
  <section class="panel patient-panel">
    <header class="panel-head">
      <p class="panel-tag">检查准备</p>
      <h2>患者信息录入</h2>
      <p class="panel-desc">录入信息后将自动进入实时测量页面，当前 Demo 为单用户单会话流程。</p>
    </header>

    <form class="form-grid" @submit.prevent="saveAndGo">
      <label class="field">
        <span>姓名</span>
        <input
          v-model.trim="form.patientName"
          class="input-control"
          type="text"
          placeholder="请输入患者姓名"
          required
        />
      </label>
      <label class="field">
        <span>病历号</span>
        <input
          v-model.trim="form.patientCode"
          class="input-control"
          type="text"
          placeholder="请输入病历号"
          required
        />
      </label>
      <label class="field">
        <span>孕周</span>
        <input
          v-model.trim="form.gestationWeek"
          class="input-control"
          type="text"
          placeholder="例如：24+3"
          required
        />
      </label>
      <button class="btn btn-primary" type="submit" :disabled="saving">保存并进入检查</button>
    </form>
    <p class="status-text">{{ message }}</p>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { createPatient } from "@/api/patients";

interface PatientForm {
  patientName: string;
  patientCode: string;
  gestationWeek: string;
}

const router = useRouter();
const message = ref("请先录入患者信息");
const saving = ref(false);

const form = reactive<PatientForm>({
  patientName: "",
  patientCode: "",
  gestationWeek: "",
});

async function saveAndGo() {
  saving.value = true;
  try {
    const patient = await createPatient({
      name: form.patientName,
      patient_code: form.patientCode,
      gestation_week: form.gestationWeek,
    });
    localStorage.setItem(
      "fetus_demo_patient",
      JSON.stringify({
        id: patient.id,
        name: patient.name,
        patientCode: patient.patient_code,
        gestationWeek: patient.gestation_week,
      }),
    );
    message.value = `已保存患者信息（ID ${patient.id}），正在进入实时测量页`;
    void router.push("/realtime");
  } catch (error) {
    message.value = error instanceof Error ? error.message : "保存失败";
  } finally {
    saving.value = false;
  }
}
</script>
