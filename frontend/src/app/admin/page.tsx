"use client";

import { useEffect, useState } from "react";
import { Bus, MapPin, TrendingUp } from "lucide-react";
import { api } from "@/lib/api";
import type { Route, Stop } from "@/lib/types";

export default function AdminDashboard() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [stops, setStops] = useState<Stop[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.routes(), api.stops()]).then(([r, s]) => {
      setRoutes(r);
      setStops(s);
      setLoading(false);
    });
  }, []);

  const stopsWithCoords = stops.filter((s) => s.lat && s.lon).length;

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Dashboard</h1>
      <p className="text-slate-400 text-sm mb-8">Resumen del sistema Urban Route AI</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6">
          <Bus className="w-6 h-6 text-blue-400 mb-3" />
          <p className="text-3xl font-bold text-white">{loading ? "—" : routes.length}</p>
          <p className="text-slate-400 text-sm mt-1">Rutas registradas</p>
        </div>
        <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6">
          <MapPin className="w-6 h-6 text-green-400 mb-3" />
          <p className="text-3xl font-bold text-white">{loading ? "—" : stops.length}</p>
          <p className="text-slate-400 text-sm mt-1">Paraderos únicos</p>
        </div>
        <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6">
          <TrendingUp className="w-6 h-6 text-yellow-400 mb-3" />
          <p className="text-3xl font-bold text-white">
            {loading ? "—" : `${stopsWithCoords}/${stops.length}`}
          </p>
          <p className="text-slate-400 text-sm mt-1">Paraderos geocodificados</p>
        </div>
      </div>

      {/* Últimas rutas */}
      <div className="bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="text-white font-semibold">Rutas recientes</h2>
        </div>
        <div className="divide-y divide-slate-800">
          {routes.slice(0, 10).map((r) => (
            <div key={r.id} className="flex items-center gap-3 px-6 py-3">
              <div className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: r.color }} />
              <span className="text-white text-sm truncate flex-1">{r.name}</span>
              {r.code && <span className="text-slate-500 text-xs font-mono">{r.code}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
