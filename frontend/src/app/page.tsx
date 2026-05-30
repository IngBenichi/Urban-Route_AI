"use client";

import { useState } from "react";
import Link from "next/link";
import { Map, Bot, Bus, ArrowRight } from "lucide-react";
import SearchBox from "@/components/search/SearchBox";
import SearchResults from "@/components/search/SearchResults";
import AIChat from "@/components/ai/AIChat";
import type { SearchResponse } from "@/lib/types";

export default function Home() {
  const [results, setResults] = useState<SearchResponse | null>(null);

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex flex-col">
      {/* Hero */}
      <section className="relative flex flex-col items-center justify-center py-20 px-4 text-center overflow-hidden">
        {/* Fondo degradado */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-950/40 via-slate-950 to-slate-950 pointer-events-none" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-blue-900/40 border border-blue-700/40 rounded-full px-4 py-1.5 text-xs text-blue-300 mb-6">
            <Bot className="w-3.5 h-3.5" />
            Powered by Grok AI
          </div>

          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 leading-tight">
            Encuentra tu ruta
            <span className="block text-blue-400">en Barranquilla</span>
          </h1>
          <p className="text-slate-400 text-lg mb-10 max-w-md mx-auto">
            Sistema inteligente de buses con IA, mapas 3D y rutas en tiempo real.
          </p>

          {/* Buscador */}
          <div className="max-w-sm mx-auto w-full">
            <SearchBox onResults={setResults} />
          </div>
        </div>
      </section>

      {/* Resultados */}
      {results && (
        <section className="max-w-2xl mx-auto w-full px-4 pb-12">
          <h2 className="text-white font-semibold mb-4">
            Resultados para{" "}
            <span className="text-blue-400">{results.origin_query}</span>
            {" → "}
            <span className="text-blue-400">{results.destination_query}</span>
          </h2>
          <SearchResults
            results={results}
            onSelectRoute={(id) => window.open(`/routes/${id}`, "_blank")}
          />
        </section>
      )}

      {/* Cards de funcionalidades */}
      {!results && (
        <section className="max-w-4xl mx-auto w-full px-4 pb-20 grid sm:grid-cols-3 gap-4 mt-4">
          <Link
            href="/map"
            className="group bg-slate-900 border border-slate-700 hover:border-blue-600 rounded-2xl p-6 transition-all"
          >
            <Map className="w-8 h-8 text-blue-400 mb-3" />
            <h3 className="text-white font-semibold mb-1">Mapa Interactivo</h3>
            <p className="text-slate-400 text-sm">Visualiza rutas en 2D y 3D sobre el mapa de Barranquilla.</p>
            <div className="mt-3 flex items-center gap-1 text-blue-400 text-xs font-medium group-hover:gap-2 transition-all">
              Abrir mapa <ArrowRight className="w-3 h-3" />
            </div>
          </Link>

          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6">
            <Bot className="w-8 h-8 text-purple-400 mb-3" />
            <h3 className="text-white font-semibold mb-1">Asistente IA</h3>
            <p className="text-slate-400 text-sm">Pregunta en lenguaje natural: &quot;¿Cómo llego al aeropuerto?&quot;</p>
            <p className="mt-3 text-purple-400 text-xs font-medium">Disponible en la esquina ↘</p>
          </div>

          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6">
            <Bus className="w-8 h-8 text-green-400 mb-3" />
            <h3 className="text-white font-semibold mb-1">100+ Rutas</h3>
            <p className="text-slate-400 text-sm">Todas las cooperativas de transporte colectivo de Barranquilla.</p>
            <p className="mt-3 text-green-400 text-xs font-medium">TRANSMETRO · COOASOATLÁN · más</p>
          </div>
        </section>
      )}

      {/* AI Chat flotante */}
      <AIChat />
    </div>
  );
}
