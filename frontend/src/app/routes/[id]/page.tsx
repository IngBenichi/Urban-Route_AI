import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Clock, MapPin, Bus } from "lucide-react";
import type { RouteWithStops } from "@/lib/types";

async function getRoute(id: string): Promise<RouteWithStops | null> {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${API_URL}/api/routes/${id}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function RouteDetailPage({ params }: { params: { id: string } }) {
  const route = await getRoute(params.id);
  if (!route) notFound();

  const stopsWithCoords = route.stops.filter((s) => s.lat && s.lon);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <Link
        href="/map"
        className="inline-flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Volver al mapa
      </Link>

      {/* Header */}
      <div className="flex items-start gap-4 mb-8">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
          style={{ backgroundColor: route.color + "33", border: `2px solid ${route.color}` }}
        >
          <Bus className="w-6 h-6" style={{ color: route.color }} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">{route.name}</h1>
          {route.code && (
            <span className="inline-block mt-1 text-xs font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
              {route.code}
            </span>
          )}
          <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              {route.stops.length} paradas
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {stopsWithCoords.length} con coordenadas
            </span>
          </div>
        </div>
      </div>

      {/* Lista de paradas */}
      <div className="bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-700">
          <h2 className="text-white font-semibold text-sm">Recorrido de la ruta</h2>
        </div>
        <ol className="divide-y divide-slate-800">
          {route.stops.map((stop, idx) => (
            <li key={stop.id} className="flex items-center gap-3 px-5 py-3">
              {/* Indicador de orden */}
              <div className="flex flex-col items-center">
                <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white"
                  style={{ backgroundColor: route.color }}
                >
                  {idx + 1}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-medium truncate">{stop.name}</p>
                {stop.lat && stop.lon ? (
                  <p className="text-slate-500 text-xs">{stop.lat.toFixed(5)}, {stop.lon.toFixed(5)}</p>
                ) : (
                  <p className="text-slate-600 text-xs italic">Sin coordenadas</p>
                )}
              </div>
              {stop.code && (
                <span className="text-xs text-slate-500 font-mono shrink-0">{stop.code}</span>
              )}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
