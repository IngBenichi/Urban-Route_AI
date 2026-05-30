"use client";

import { Clock, MapPin, ArrowRight, Bus } from "lucide-react";
import type { SearchResponse } from "@/lib/types";

interface Props {
  results: SearchResponse;
  onSelectRoute?: (routeId: number) => void;
}

function Badge({ text, color }: { text: string; color: string }) {
  return (
    <span
      className="inline-block text-xs font-bold px-2 py-0.5 rounded-full text-white"
      style={{ backgroundColor: color }}
    >
      {text}
    </span>
  );
}

export default function SearchResults({ results, onSelectRoute }: Props) {
  if (results.total_results === 0) {
    return (
      <div className="text-slate-400 text-sm py-4 text-center">
        No se encontraron rutas entre esos puntos.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 max-h-96 overflow-y-auto pr-1">
      {/* ── Directas ────────────────────────────────────────────── */}
      {results.direct.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Rutas directas ({results.direct.length})
          </h3>
          {results.direct.map((r, i) => (
            <button
              key={`direct-${i}`}
              onClick={() => onSelectRoute?.(r.route.id)}
              className="w-full text-left bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-xl p-3 mb-2 transition-colors"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2 min-w-0">
                  <Bus className="w-4 h-4 shrink-0" style={{ color: r.route.color }} />
                  <span className="text-white text-sm font-medium truncate">{r.route.name}</span>
                </div>
                <Badge text="Directo" color={r.route.color} />
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {r.time_min} min
                </span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {r.distance_km} km
                </span>
              </div>
              <div className="flex items-center gap-1 mt-1.5 text-xs text-slate-400 truncate">
                <span className="truncate">{r.from_stop.name}</span>
                <ArrowRight className="w-3 h-3 shrink-0" />
                <span className="truncate">{r.to_stop.name}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* ── Con transbordo ──────────────────────────────────────── */}
      {results.transfers.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Con transbordo ({results.transfers.length})
          </h3>
          {results.transfers.map((r, i) => (
            <div
              key={`transfer-${i}`}
              className="bg-slate-800 border border-slate-600 rounded-xl p-3 mb-2"
            >
              <div className="flex items-center gap-2 mb-1">
                <Bus className="w-3 h-3" style={{ color: r.route_a.color }} />
                <span className="text-white text-xs font-medium truncate">{r.route_a.name}</span>
              </div>
              <div className="flex items-center gap-1 text-xs text-yellow-400 px-1 mb-1">
                <ArrowRight className="w-3 h-3" />
                Transbordo: {r.transfer_stop.name}
              </div>
              <div className="flex items-center gap-2 mb-2">
                <Bus className="w-3 h-3" style={{ color: r.route_b.color }} />
                <span className="text-white text-xs font-medium truncate">{r.route_b.name}</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {r.time_min} min
                </span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {r.distance_km} km
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
