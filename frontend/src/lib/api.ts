import type {
  Stop,
  Route,
  RouteWithStops,
  SearchResponse,
  AIResponse,
  TokenResponse,
  RoutePlan,
} from "@/lib/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options?: RequestInit & { token?: string }
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (options?.token) {
    headers["Authorization"] = `Bearer ${options.token}`;
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { token: _token, ...fetchOptions } = options ?? {};

  const res = await fetch(`${API_URL}${path}`, {
    ...fetchOptions,
    headers: { ...headers, ...(fetchOptions.headers ?? {}) },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? "Error de API");
  }

  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

export const api = {
  // ── Búsqueda ────────────────────────────────────────────────────────────────
  search: (origin: string, destination: string): Promise<SearchResponse> =>
    apiFetch("/api/search", {
      method: "POST",
      body: JSON.stringify({ origin, destination }),
    }),

  // ── Rutas ───────────────────────────────────────────────────────────────────
  routes: (): Promise<Route[]> => apiFetch("/api/routes"),

  route: (id: number): Promise<RouteWithStops> =>
    apiFetch(`/api/routes/${id}`),

  createRoute: (body: object, token: string): Promise<Route> =>
    apiFetch("/api/routes", { method: "POST", body: JSON.stringify(body), token }),

  updateRoute: (id: number, body: object, token: string): Promise<Route> =>
    apiFetch(`/api/routes/${id}`, { method: "PUT", body: JSON.stringify(body), token }),

  deleteRoute: (id: number, token: string): Promise<void> =>
    apiFetch(`/api/routes/${id}`, { method: "DELETE", token }),

  // ── Paraderos ────────────────────────────────────────────────────────────────
  stops: (q?: string): Promise<Stop[]> =>
    apiFetch(`/api/stops${q ? `?q=${encodeURIComponent(q)}&limit=8` : "?limit=100"}`),

  stop: (id: number): Promise<Stop> => apiFetch(`/api/stops/${id}`),

  createStop: (body: object, token: string): Promise<Stop> =>
    apiFetch("/api/stops", { method: "POST", body: JSON.stringify(body), token }),

  updateStop: (id: number, body: object, token: string): Promise<Stop> =>
    apiFetch(`/api/stops/${id}`, { method: "PUT", body: JSON.stringify(body), token }),

  deleteStop: (id: number, token: string): Promise<void> =>
    apiFetch(`/api/stops/${id}`, { method: "DELETE", token }),

  // ── IA ──────────────────────────────────────────────────────────────────────
  aiRecommend: (query: string, context?: string): Promise<AIResponse> =>
    apiFetch("/api/ai/recommend", {
      method: "POST",
      body: JSON.stringify({ query, context: context ?? "" }),
    }),

  // ── Planificación de ruta ────────────────────────────────────────────────────
  planRoute: (destination: string, originLat: number, originLon: number): Promise<RoutePlan> =>
    apiFetch("/api/search/plan", {
      method: "POST",
      body: JSON.stringify({ destination, origin_lat: originLat, origin_lon: originLon }),
    }),

  // ── Auth ────────────────────────────────────────────────────────────────────
  login: (username: string, password: string): Promise<TokenResponse> =>
    apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
};
