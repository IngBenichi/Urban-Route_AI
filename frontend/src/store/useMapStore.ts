import { create } from "zustand";
import type { RouteWithStops, SearchResponse } from "@/lib/types";

interface MapStore {
  // Mapa
  mapLoaded: boolean;
  setMapLoaded: (loaded: boolean) => void;

  // Vista 3D
  is3D: boolean;
  toggle3D: () => void;

  // Búsqueda
  origin: string;
  destination: string;
  setOrigin: (v: string) => void;
  setDestination: (v: string) => void;

  // Resultados
  searchResults: SearchResponse | null;
  setSearchResults: (r: SearchResponse | null) => void;

  // Ruta seleccionada en el mapa
  selectedRoute: RouteWithStops | null;
  setSelectedRoute: (r: RouteWithStops | null) => void;

  // Panel IA
  aiPanelOpen: boolean;
  toggleAIPanel: () => void;
}

export const useMapStore = create<MapStore>((set) => ({
  mapLoaded: false,
  setMapLoaded: (loaded) => set({ mapLoaded: loaded }),

  is3D: false,
  toggle3D: () => set((s) => ({ is3D: !s.is3D })),

  origin: "",
  destination: "",
  setOrigin: (v) => set({ origin: v }),
  setDestination: (v) => set({ destination: v }),

  searchResults: null,
  setSearchResults: (r) => set({ searchResults: r }),

  selectedRoute: null,
  setSelectedRoute: (r) => set({ selectedRoute: r }),

  aiPanelOpen: false,
  toggleAIPanel: () => set((s) => ({ aiPanelOpen: !s.aiPanelOpen })),
}));
