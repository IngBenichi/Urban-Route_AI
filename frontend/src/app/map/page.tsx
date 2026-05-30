"use client";

import dynamic from "next/dynamic";
import { useState, useCallback, useRef } from "react";
import { Navigation } from "lucide-react";
import SearchResults from "@/components/search/SearchResults";
import RoutePlanCard from "@/components/search/RoutePlanCard";
import AIChat from "@/components/ai/AIChat";
import type { SearchResponse, RouteWithStops, RoutePlan } from "@/lib/types";
import { api } from "@/lib/api";

// Leaflet solo en el cliente
const LeafletMap = dynamic(() => import("@/components/map/LeafletMap"), { ssr: false });
const RouteLayer = dynamic(() => import("@/components/map/RouteLayer"), { ssr: false });
const PlanLayer = dynamic(() => import("@/components/map/PlanLayer"), { ssr: false });

export default function MapPage() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [map, setMap] = useState<any>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [activeRoute, setActiveRoute] = useState<RouteWithStops | null>(null);
  const [plan, setPlan] = useState<RoutePlan | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [destination, setDestination] = useState("");
  const userLatRef = useRef<number | null>(null);
  const userLonRef = useRef<number | null>(null);
  const [hasGps, setHasGps] = useState(false);
  // Coordenadas de origen guardadas al momento de calcular el plan
  const [planOrigin, setPlanOrigin] = useState<{ lat: number; lon: number } | null>(null);

  const handleMapReady = useCallback((m: unknown) => setMap(m), []);

  const handleLocationUpdate = useCallback((lat: number, lon: number) => {
    userLatRef.current = lat;
    userLonRef.current = lon;
    setHasGps(true);
  }, []);

  const handleSelectRoute = async (routeId: number) => {
    const route = await api.route(routeId).catch(() => null);
    if (!route) return;
    setActiveRoute(route);
    setPlan(null);
  };

  const handlePlan = async () => {
    if (!destination.trim()) return;
    if (userLatRef.current === null || userLonRef.current === null) {
      alert("Activa el GPS — permite la ubicación en el navegador.");
      return;
    }
    const originLat = userLatRef.current;
    const originLon = userLonRef.current;
    setPlanLoading(true);
    setPlan(null);
    setPlanOrigin(null);
    setResults(null);
    try {
      const result = await api.planRoute(destination, originLat, originLon);
      setPlan(result);
      if (result.found) {
        setPlanOrigin({ lat: originLat, lon: originLon });
      }
    } finally {
      setPlanLoading(false);
    }
  };

  return (
    <div className="relative h-[calc(100vh-3.5rem)] flex overflow-hidden">
      {/* Panel lateral */}
      <aside className="w-80 shrink-0 bg-slate-950 border-r border-slate-800 flex flex-col overflow-hidden z-10">
        <div className="p-4 border-b border-slate-800">
          <h1 className="text-white font-semibold text-sm mb-3">¿A dónde quieres ir?</h1>

          {/* Indicador GPS */}
          <div className={`flex items-center gap-1.5 text-xs mb-3 ${hasGps ? "text-green-400" : "text-slate-500"}`}>
            <span className={`w-2 h-2 rounded-full ${hasGps ? "bg-green-400 animate-pulse" : "bg-slate-600"}`} />
            {hasGps ? "GPS activo — tu ubicación está en el mapa" : "Esperando GPS…"}
          </div>

          {/* Campo de destino */}
          <div className="flex gap-2">
            <input
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handlePlan()}
              placeholder="Malecón del Río, Centro…"
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={handlePlan}
              disabled={planLoading || !destination.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-3 py-2 rounded-lg transition-colors"
            >
              <Navigation className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Plan de ruta */}
          {(planLoading || plan) && (
            <RoutePlanCard plan={plan ?? { found: false, destination_name: destination, steps: [], total_time_min: 0 }} loading={planLoading} />
          )}

          {/* Resultados de búsqueda clásica */}
          {results && !plan && !planLoading && (
            <SearchResults results={results} onSelectRoute={handleSelectRoute} />
          )}

          {!planLoading && !plan && !results && (
            <div className="text-slate-500 text-xs text-center mt-8 px-4">
              Escribe tu destino arriba y el sistema te dirá qué bus tomar y dónde subirte.
            </div>
          )}
        </div>
      </aside>

      {/* Mapa */}
      <div className="flex-1 relative">
        <LeafletMap
          onMapReady={handleMapReady}
          onLocationUpdate={handleLocationUpdate}
          className="w-full h-full"
        />

        {activeRoute && map && !plan && (
          <RouteLayer map={map} route={activeRoute} isActive />
        )}

        {plan && plan.found && planOrigin && map && (
          <PlanLayer
            map={map}
            plan={plan}
            userLat={planOrigin.lat}
            userLon={planOrigin.lon}
          />
        )}
      </div>

      <AIChat />
    </div>
  );
}
