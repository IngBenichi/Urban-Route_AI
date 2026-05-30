"use client";

import { useEffect, useRef } from "react";
import type { RouteWithStops } from "@/lib/types";

interface Props {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  map: any | null;
  route: RouteWithStops;
  isActive?: boolean;
}

export default function RouteLayer({ map, route }: Props) {
  const layersRef = useRef<unknown[]>([]);

  useEffect(() => {
    if (!map) return;

    const initLayer = async () => {
      const L = (await import("leaflet")).default;

      // Limpiar capas anteriores
      layersRef.current.forEach((l) => (l as import("leaflet").Layer).remove());
      layersRef.current = [];

      const stops = route.stops
        .filter((s) => s.lat != null && s.lon != null)
        .sort((a, b) => a.order_index - b.order_index);

      if (stops.length < 2) return;

      const latlngs: [number, number][] = stops.map((s) => [s.lat!, s.lon!]);

      // Línea de la ruta
      const polyline = L.polyline(latlngs, {
        color: route.color ?? "#3B82F6",
        weight: 4,
        opacity: 0.85,
      }).addTo(map);
      layersRef.current.push(polyline);

      // Círculos en cada paradero
      stops.forEach((stop, idx) => {
        const isEndpoint = idx === 0 || idx === stops.length - 1;
        const circle = L.circleMarker([stop.lat!, stop.lon!], {
          radius: isEndpoint ? 8 : 5,
          color: "#ffffff",
          weight: 2,
          fillColor: route.color ?? "#3B82F6",
          fillOpacity: 1,
        })
          .bindPopup(
            `<div style="font-size:12px;font-weight:600">${stop.name}</div>`,
            { maxWidth: 200 }
          )
          .addTo(map);
        layersRef.current.push(circle);
      });

      // Centrar mapa en la ruta
      map.fitBounds(polyline.getBounds(), { padding: [40, 40] });
    };

    initLayer();

    return () => {
      layersRef.current.forEach((l) => (l as import("leaflet").Layer).remove());
      layersRef.current = [];
    };
  }, [map, route]);

  return null;
}
