import { getToken } from "@/auth/session";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
export const MEDIA_BASE_URL =
  import.meta.env.VITE_MEDIA_BASE_URL ?? API_BASE_URL.replace(/\/api\/v1\/?$/, "");

function authHeaders(): Record<string, string> {
  const token = getToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

function normalizeDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const texts = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") return item.msg;
        return "";
      })
      .filter(Boolean);
    return texts.join("；");
  }
  if (detail && typeof detail === "object") {
    if ("msg" in detail && typeof detail.msg === "string") return detail.msg;
    return "请求参数格式错误";
  }
  return "";
}

function statusFallback(status: number): string {
  if (status === 400) return "请求参数不合法";
  if (status === 401) return "未登录或登录已失效，请重新登录";
  if (status === 403) return "没有权限执行该操作";
  if (status === 404) return "请求资源不存在";
  if (status === 409) return "当前状态不允许此操作";
  if (status >= 500) return "服务暂时不可用，请稍后重试";
  return "请求失败";
}

async function buildApiError(res: Response): Promise<Error> {
  let detailText = "";
  const contentType = res.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      const data = (await res.json()) as { detail?: unknown };
      detailText = normalizeDetail(data.detail);
    } catch {
      detailText = "";
    }
  } else {
    try {
      const text = (await res.text()).trim();
      detailText = text || "";
    } catch {
      detailText = "";
    }
  }

  const message = detailText || statusFallback(res.status);
  return new Error(message);
}

export async function apiGet<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { headers: authHeaders() });
  } catch {
    throw new Error("网络连接失败，请确认后端服务已启动");
  }

  if (!res.ok) {
    throw await buildApiError(res);
  }
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error("网络连接失败，请确认后端服务已启动");
  }

  if (!res.ok) {
    throw await buildApiError(res);
  }
  return (await res.json()) as T;
}

export async function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });
  } catch {
    throw new Error("网络连接失败，请确认后端服务已启动");
  }

  if (!res.ok) {
    throw await buildApiError(res);
  }
  return (await res.json()) as T;
}

export function resolveMediaUrl(pathOrUrl: string): string {
  if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
    return pathOrUrl;
  }
  if (pathOrUrl.startsWith("/")) {
    return `${MEDIA_BASE_URL}${pathOrUrl}`;
  }
  return `${MEDIA_BASE_URL}/${pathOrUrl}`;
}
