import { apiGet, apiPost } from "@/api/http";
import { clearAuth, setAuth, type LoginUser } from "@/auth/session";

interface AuthResponse {
  token: string;
  user: LoginUser;
}

export function register(username: string, password: string): Promise<AuthResponse> {
  return apiPost<AuthResponse>("/auth/register", { username, password }).then((res) => {
    setAuth(res.token, res.user);
    return res;
  });
}

export function login(username: string, password: string): Promise<AuthResponse> {
  return apiPost<AuthResponse>("/auth/login", { username, password }).then((res) => {
    setAuth(res.token, res.user);
    return res;
  });
}

export function logout(): Promise<void> {
  return apiPost<{ message: string }>("/auth/logout")
    .then(() => {
      clearAuth();
    })
    .catch(() => {
      clearAuth();
    });
}

export function me(): Promise<LoginUser> {
  return apiGet<LoginUser>("/auth/me");
}
