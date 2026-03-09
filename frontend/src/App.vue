<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="brand-block">
        <p class="brand-kicker">医学辅助分析 Demo</p>
        <h1>胎儿超声视频流实时解译系统</h1>
      </div>
      <div class="header-actions">
        <nav v-if="loggedIn" class="nav-tabs">
          <RouterLink to="/patient">患者信息</RouterLink>
          <RouterLink to="/realtime">实时测量</RouterLink>
          <RouterLink to="/history">历史记录</RouterLink>
        </nav>
        <button v-if="loggedIn" class="btn btn-danger logout-btn" @click="handleLogout">退出系统</button>
      </div>
    </header>

    <main class="page-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { logout } from "@/api/auth";
import { clearAuth, isLoggedIn } from "@/auth/session";

const router = useRouter();
const route = useRoute();
const loggedIn = computed(() => {
  route.fullPath;
  return isLoggedIn();
});

async function handleLogout() {
  await logout();
  clearAuth();
  localStorage.removeItem("fetus_demo_patient");
  void router.push("/login");
}
</script>
