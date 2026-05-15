import axios, { AxiosError } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";

// VITE_API_URL이 설정된 경우(Docker 등) 직접 요청, 없으면 "" (상대경로 → Vite proxy 경유)
const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// ─── Request interceptor: log every outgoing call ────────────────────────────
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  (config as InternalAxiosRequestConfig & { _t: number })._t = performance.now();
  return config;
});

// ─── Response interceptor: log timing and errors ─────────────────────────────
apiClient.interceptors.response.use(
  (res: AxiosResponse) => {
    return res;
  },
  (err: AxiosError) => {
    const cfg = err.config as (InternalAxiosRequestConfig & { _t: number }) | undefined;
    const ms = cfg?._t ? Math.round(performance.now() - cfg._t) : -1;
    console.error(`[API] ✗ ${err.config?.url} (${ms}ms)`, err.response?.data ?? err.message);
    return Promise.reject(err);
  }
);
