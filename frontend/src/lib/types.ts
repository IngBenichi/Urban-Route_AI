// ─── Modelos del dominio ──────────────────────────────────────────────────────

export interface Stop {
  id: number;
  name: string;
  lat: number | null;
  lon: number | null;
  code: string | null;
}

export interface StopInRoute extends Stop {
  order_index: number;
}

export interface Route {
  id: number;
  name: string;
  code: string | null;
  color: string;
  created_at: string;
}

export interface RouteWithStops extends Route {
  stops: StopInRoute[];
}

// ─── Búsqueda ─────────────────────────────────────────────────────────────────

export interface DirectRouteResult {
  route: Route;
  from_stop: Stop;
  to_stop: Stop;
  stops_sequence: Stop[];
  distance_km: number;
  time_min: number;
}

export interface TransferRouteResult {
  route_a: Route;
  route_b: Route;
  from_stop: Stop;
  transfer_stop: Stop;
  to_stop: Stop;
  distance_km: number;
  time_min: number;
}

export interface SearchResponse {
  origin_query: string;
  destination_query: string;
  direct: DirectRouteResult[];
  transfers: TransferRouteResult[];
  total_results: number;
}

// ─── IA ───────────────────────────────────────────────────────────────────────

export interface AIResponse {
  answer: string;
  query: string;
}

// ─── Planificación de ruta ────────────────────────────────────────────────────

export interface RouteStep {
  type: "walk" | "bus";
  instruction: string;
  distance_m?: number;
  stop_name?: string;
  stop_lat?: number;
  stop_lon?: number;
  route_name?: string;
  route_color?: string;
}

export interface RoutePlan {
  found: boolean;
  destination_name: string;
  dest_lat?: number;
  dest_lon?: number;
  steps: RouteStep[];
  total_time_min: number;
  ai_narration?: string;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
