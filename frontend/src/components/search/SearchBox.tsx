"use client";

import { useState, useCallback, useRef } from "react";
import { Search, MapPin, ArrowRightLeft } from "lucide-react";
import { api } from "@/lib/api";
import type { Stop, SearchResponse } from "@/lib/types";

interface Props {
  onResults: (r: SearchResponse) => void;
  className?: string;
}

function useDebounce<T extends (...args: unknown[]) => void>(fn: T, delay: number) {
  const timer = useRef<ReturnType<typeof setTimeout>>();
  return useCallback(
    (...args: Parameters<T>) => {
      clearTimeout(timer.current);
      timer.current = setTimeout(() => fn(...args), delay);
    },
    [fn, delay]
  );
}

export default function SearchBox({ onResults, className = "" }: Props) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [originSuggestions, setOriginSuggestions] = useState<Stop[]>([]);
  const [destSuggestions, setDestSuggestions] = useState<Stop[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchSuggestions = useCallback(
    async (q: string, setter: (stops: Stop[]) => void) => {
      if (q.trim().length < 2) { setter([]); return; }
      const stops = await api.stops(q).catch(() => []);
      setter(stops.slice(0, 6));
    },
    []
  );

  const debouncedOrigin = useDebounce(
    (q: unknown) => fetchSuggestions(q as string, setOriginSuggestions),
    300
  );
  const debouncedDest = useDebounce(
    (q: unknown) => fetchSuggestions(q as string, setDestSuggestions),
    300
  );

  const swap = () => {
    setOrigin(destination);
    setDestination(origin);
    setOriginSuggestions([]);
    setDestSuggestions([]);
  };

  const handleSearch = async () => {
    if (!origin.trim() || !destination.trim()) {
      setError("Ingresa origen y destino.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const results = await api.search(origin.trim(), destination.trim());
      onResults(results);
      if (results.total_results === 0) {
        setError("No se encontraron rutas. Intenta con otros nombres.");
      }
    } catch {
      setError("Error al buscar rutas. Verifica la conexión.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`bg-slate-900/95 backdrop-blur rounded-2xl p-4 shadow-2xl border border-slate-700 ${className}`}>
      <h2 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
        <Search className="w-4 h-4 text-blue-400" />
        Buscar ruta
      </h2>

      <div className="flex flex-col gap-2">
        {/* Origen */}
        <div className="relative">
          <div className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2 border border-slate-600 focus-within:border-blue-500">
            <MapPin className="w-4 h-4 text-green-400 shrink-0" />
            <input
              type="text"
              placeholder="¿Desde dónde?"
              value={origin}
              className="bg-transparent text-white text-sm outline-none w-full placeholder:text-slate-400"
              onChange={(e) => {
                setOrigin(e.target.value);
                debouncedOrigin(e.target.value);
              }}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          {originSuggestions.length > 0 && (
            <ul className="absolute z-50 top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-xl overflow-hidden">
              {originSuggestions.map((s) => (
                <li
                  key={s.id}
                  className="px-3 py-2 text-sm text-white hover:bg-slate-700 cursor-pointer"
                  onMouseDown={() => { setOrigin(s.name); setOriginSuggestions([]); }}
                >
                  {s.name}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Botón swap */}
        <div className="flex justify-center">
          <button
            onClick={swap}
            className="p-1 text-slate-400 hover:text-white transition-colors"
            title="Intercambiar origen y destino"
          >
            <ArrowRightLeft className="w-4 h-4" />
          </button>
        </div>

        {/* Destino */}
        <div className="relative">
          <div className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2 border border-slate-600 focus-within:border-blue-500">
            <MapPin className="w-4 h-4 text-red-400 shrink-0" />
            <input
              type="text"
              placeholder="¿A dónde vas?"
              value={destination}
              className="bg-transparent text-white text-sm outline-none w-full placeholder:text-slate-400"
              onChange={(e) => {
                setDestination(e.target.value);
                debouncedDest(e.target.value);
              }}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          {destSuggestions.length > 0 && (
            <ul className="absolute z-50 top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-xl overflow-hidden">
              {destSuggestions.map((s) => (
                <li
                  key={s.id}
                  className="px-3 py-2 text-sm text-white hover:bg-slate-700 cursor-pointer"
                  onMouseDown={() => { setDestination(s.name); setDestSuggestions([]); }}
                >
                  {s.name}
                </li>
              ))}
            </ul>
          )}
        </div>

        {error && <p className="text-red-400 text-xs">{error}</p>}

        <button
          onClick={handleSearch}
          disabled={loading}
          className="mt-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg py-2.5 transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <span className="animate-pulse">Buscando...</span>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Buscar
            </>
          )}
        </button>
      </div>
    </div>
  );
}
