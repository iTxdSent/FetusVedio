const TOKEN_KEY = "fetus_demo_token";
const USER_KEY = "fetus_demo_user";

export interface LoginUser {
  id: number;
  username: string;
  created_at: string;
}

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setAuth(token: string, user: LoginUser): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getUser(): LoginUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as LoginUser;
  } catch {
    return null;
  }
}

export function isLoggedIn(): boolean {
  return Boolean(getToken());
}
