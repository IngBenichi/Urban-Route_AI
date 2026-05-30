"use client";

import { useEffect, useRef } from "react";
import type { RoutePlan } from "@/lib/types";

interface Props {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  map: any | null;
  plan: RoutePlan;
  userLat: number;
  userLon: number;
}

type LatLng = [number, number]; // [lat, lon]

/** Pide geometría real de carretera a OSRM. Fallback: línea recta. */
async function fetchRoadGeometry(
  from: LatLng,
  to: LatLng,
  profile: "driving" | "foot" = "driving"
): Promise<LatLng[]> {
  try {
    // OSRM espera lon,lat en la URL; devuelve [lon,lat] en GeoJSON
    const base =
      profile === "foot"
        ? "https://routing.openstreetmap.de/routed-foot/route/v1/foot"
        : "https://router.project-osrm.org/route/v1/driving";
    const url = `${base}/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);

    if (!res.ok) throw new Error("OSRM HTTP " + res.status);
    const data = await res.json();
    const coords = data.routes[0].geometry.coordinates as [number, number][];
    return coords.map(([lon, lat]) => [lat, lon] as LatLng);
  } catch {
    // Fallback: línea directa si el servicio falla
    return [from, to];
  }
}

export default function PlanLayer({ map, plan, userLat, userLon }: Props) {
  const layersRef = useRef<unknown[]>([]);

  useEffect(() => {
    if (!map || !plan.found) return;
    if (!plan.dest_lat || !plan.dest_lon) return;

    const draw = async () => {
      const L = (await import("leaflet")).default;

      // Limpiar capas anteriores
      layersRef.current.forEach((l) => (l as import("leaflet").Layer).remove());
      layersRef.current = [];

      const steps = plan.steps;
      const walkStep1 = steps[0]; // caminar al paradero de subida
      const busStep = steps[1];   // tomar el bus
      const walkStep2 = steps[2]; // caminar desde paradero de bajada

      if (!walkStep1?.stop_lat || !busStep?.stop_lat || !walkStep2?.stop_lat) return;

      const boardingLat = walkStep1.stop_lat;
      const boardingLon = walkStep1.stop_lon!;
      const alightingLat = walkStep2.stop_lat;
      const alightingLon = walkStep2.stop_lon!;
      const busColor = busStep.route_color ?? "#10B981";

      // Pedir geometría real a OSRM en paralelo
      const [walkPath1, busPath, walkPath2] = await Promise.all([
        fetchRoadGeometry([userLat, userLon], [boardingLat, boardingLon], "foot"),
        fetchRoadGeometry([boardingLat, boardingLon], [alightingLat, alightingLon], "driving"),
        fetchRoadGeometry([alightingLat, alightingLon], [plan.dest_lat!, plan.dest_lon!], "foot"),
      ]);

      // ── Caminata 1: puntos redondeados estilo "footsteps" ──────────────
      const walk1Shadow = L.polyline(walkPath1, {
        color: "#fff",
        weight: 9,
        opacity: 0.5,
        lineCap: "round" as const,
      }).addTo(map);
      layersRef.current.push(walk1Shadow);

      const walk1Line = L.polyline(walkPath1, {
        color: "#374151",
        weight: 5,
        opacity: 0.85,
        dashArray: "1 13",
        lineCap: "round" as const,
      }).addTo(map);
      layersRef.current.push(walk1Line);

      // ── Ruta de bus: línea sólida gruesa con el color de la ruta ─────
      const busBorder = L.polyline(busPath, {
        color: "#fff",
        weight: 8,
        opacity: 0.4,
      }).addTo(map);
      layersRef.current.push(busBorder);

      const busLine = L.polyline(busPath, {
        color: busColor,
        weight: 5,
        opacity: 1,
      }).addTo(map);
      layersRef.current.push(busLine);

      // ── Caminata 2: puntos redondeados estilo "footsteps" ──────────────
      const walk2Shadow = L.polyline(walkPath2, {
        color: "#fff",
        weight: 9,
        opacity: 0.5,
        lineCap: "round" as const,
      }).addTo(map);
      layersRef.current.push(walk2Shadow);

      const walk2Line = L.polyline(walkPath2, {
        color: "#374151",
        weight: 5,
        opacity: 0.85,
        dashArray: "1 13",
        lineCap: "round" as const,
      }).addTo(map);
      layersRef.current.push(walk2Line);

      // ── Marcador de subida ────────────────────────────────────────────
      const boardingCircle = L.circleMarker([boardingLat, boardingLon], {
        radius: 9,
        color: "#fff",
        weight: 2.5,
        fillColor: busColor,
        fillOpacity: 1,
      })
        .bindPopup(
          `<div style="font-size:12px"><b>🚌 Subida</b><br>${walkStep1.stop_name ?? ""}</div>`
        )
        .addTo(map);
      layersRef.current.push(boardingCircle);

      // ── Marcador de bajada ────────────────────────────────────────────
      const alightingCircle = L.circleMarker([alightingLat, alightingLon], {
        radius: 9,
        color: "#fff",
        weight: 2.5,
        fillColor: busColor,
        fillOpacity: 1,
      })
        .bindPopup(
          `<div style="font-size:12px"><b>🚏 Bajada</b><br>${walkStep2.stop_name ?? ""}</div>`
        )
        .addTo(map);
      layersRef.current.push(alightingCircle);

      // ── Marcador de destino (pin rojo) ────────────────────────────────
      const destIcon = L.divIcon({
        html: `<div style="
          background:#EF4444;
          width:18px;height:18px;
          border-radius:50% 50% 50% 0;
          transform:rotate(-45deg);
          border:2.5px solid #fff;
          box-shadow:0 2px 6px rgba(0,0,0,0.5)
        "></div>`,
        className: "",
        iconSize: [18, 18],
        iconAnchor: [9, 18],
      });
      const destMarker = L.marker([plan.dest_lat!, plan.dest_lon!], {
        icon: destIcon,
      })
        .bindPopup(
          `<div style="font-size:12px"><b>📍 ${plan.destination_name.split(",")[0]}</b></div>`
        )
        .openPopup()
        .addTo(map);
      layersRef.current.push(destMarker);

      // ── Ajustar vista del mapa ────────────────────────────────────────
      const allPoints: LatLng[] = [
        [userLat, userLon],
        ...walkPath1,
        ...busPath,
        ...walkPath2,
        [plan.dest_lat!, plan.dest_lon!],
      ];
      map.fitBounds(L.latLngBounds(allPoints), { padding: [50, 60] });
    };

    draw();

    return () => {
      layersRef.current.forEach((l) => (l as import("leaflet").Layer).remove());
      layersRef.current = [];
    };
  }, [map, plan, userLat, userLon]);

  return null;
}
