import { createRouter, createWebHistory } from "vue-router";

import { isLoggedIn } from "@/auth/session";
import HistoryPage from "@/views/HistoryPage.vue";
import LoginPage from "@/views/LoginPage.vue";
import PatientInfoPage from "@/views/PatientInfoPage.vue";
import RealtimePage from "@/views/RealtimePage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/patient" },
    { path: "/login", name: "login", component: LoginPage, meta: { public: true } },
    { path: "/patient", name: "patient", component: PatientInfoPage },
    { path: "/realtime", name: "realtime", component: RealtimePage },
    { path: "/history", name: "history", component: HistoryPage },
  ],
});

router.beforeEach((to) => {
  const isPublic = Boolean(to.meta.public);
  if (!isPublic && !isLoggedIn()) {
    return { path: "/login" };
  }
  if (to.path === "/login" && isLoggedIn()) {
    return { path: "/patient" };
  }
  return true;
});

export default router;
