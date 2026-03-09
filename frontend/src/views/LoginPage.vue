<template>
  <section class="panel auth-panel">
    <header class="panel-head">
      <p class="panel-tag">用户认证</p>
      <h2>登录系统</h2>
      <p class="panel-desc">未登录或登录失败时，无法访问患者录入、实时测量和历史查询功能。</p>
    </header>

    <form class="form-grid" @submit.prevent="handleLogin">
      <label class="field">
        <span>用户名</span>
        <input v-model.trim="username" class="input-control" type="text" required />
      </label>
      <label class="field">
        <span>密码</span>
        <input v-model="password" class="input-control" type="password" required />
      </label>
      <div class="btn-row">
        <button class="btn btn-primary" type="submit" :disabled="busy">登录</button>
        <button class="btn btn-secondary" type="button" :disabled="busy" @click="handleRegister">注册并登录</button>
      </div>
    </form>
    <p class="status-text">{{ message }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { login, register } from "@/api/auth";

const router = useRouter();
const username = ref("");
const password = ref("");
const busy = ref(false);
const message = ref("请先登录，未登录无法进入主功能");

async function handleLogin() {
  busy.value = true;
  try {
    await login(username.value, password.value);
    message.value = "登录成功";
    void router.push("/patient");
  } catch (error) {
    message.value = error instanceof Error ? error.message : "登录失败";
  } finally {
    busy.value = false;
  }
}

async function handleRegister() {
  busy.value = true;
  try {
    await register(username.value, password.value);
    message.value = "注册并登录成功";
    void router.push("/patient");
  } catch (error) {
    message.value = error instanceof Error ? error.message : "注册失败";
  } finally {
    busy.value = false;
  }
}
</script>
