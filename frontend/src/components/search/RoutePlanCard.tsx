"use client";

import { useState } from "react";
import { Navigation, Bus, Footprints, Clock, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import type { RoutePlan } from "@/lib/types";

interface Props {
  plan: RoutePlan;
  loading?: boolean;
}

export default function RoutePlanCard({ plan, loading }: Props) {
  const [showAI, setShowAI] = useState(false);

  if (loading) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-700 p-4 space-y-3">
        <div className="flex items-center gap-2 text-blue-400 text-sm font-medium">
          <Navigation className="w-4 h-4 animate-pulse" />
          Planificando tu ruta...
        </div>
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-10 bg-slate-800 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (!plan.found) {
    return (
      <div className="bg-red-950/40 border border-red-800 rounded-xl p-4 text-sm text-red-300">
        No encontré rutas de bus hacia <strong>{plan.destination_name}</strong>.
        Intenta con un nombre más específico o un barrio cercano.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-blue-600/20 border-b border-blue-600/30 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-blue-400" />
          <span className="text-white text-sm font-semibold truncate max-w-[180px]">
            {plan.destination_name.split(",")[0]}
          </span>
        </div>
        <div className="flex items-center gap-1 text-slate-300 text-xs">
          <Clock className="w-3.5 h-3.5" />
          ~{plan.total_time_min} min
        </div>
      </div>

      {/* Steps */}
      <div className="p-3 space-y-2">
        {plan.steps.map((step, i) => (
          <div key={i} className={`flex gap-3 p-2.5 rounded-lg ${
            step.type === "bus"
              ? "bg-slate-800 border border-slate-700"
              : "bg-slate-800/40"
          }`}>
            {/* Ícono */}
            <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
              step.type === "bus" ? "bg-blue-600" : "bg-slate-700"
            }`}>
              {step.type === "bus"
                ? <Bus className="w-3.5 h-3.5 text-white" />
                : <Footprints className="w-3.5 h-3.5 text-slate-300" />
              }
            </div>

            {/* Contenido */}
            <div className="flex-1 min-w-0">
              <p className="text-white text-xs leading-snug">{step.instruction}</p>
              {step.type === "bus" && step.route_color && (
                <span
                  className="inline-block mt-1 px-2 py-0.5 rounded text-white text-[10px] font-bold"
                  style={{ background: step.route_color }}
                >
                  {step.route_name}
                </span>
              )}
              {step.type === "walk" && step.distance_m !== undefined && (
                <span className="text-slate-400 text-[10px]">
                  {step.distance_m < 1000
                    ? `${step.distance_m}m caminando`
                    : `${(step.distance_m / 1000).toFixed(1)}km caminando`}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Narración IA */}
      {plan.ai_narration && (
        <div className="border-t border-slate-700">
          <button
            onClick={() => setShowAI((v) => !v)}
            className="w-full px-4 py-2.5 flex items-center justify-between text-xs text-purple-300 hover:bg-slate-800 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Explicación de la IA
            </span>
            {showAI ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          {showAI && (
            <div className="px-4 pb-4 text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
              {plan.ai_narration}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
