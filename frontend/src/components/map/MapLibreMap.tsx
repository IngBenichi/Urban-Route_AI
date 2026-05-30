"use client";

import { useEffect, useRef, useCallback } from "react";

const BARRANQUILLA: [number, number] = [-74.7964, 10.9878];

interface Props {
  onMapReady?: (map: unknown) => void;
  className?: string;
  pitch?: number;
}

export default function MapLibreMap({ onMapReady, className = "w-full h-full", pitch = 0 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);

  const initMap = useCallback(async () => {
    if (!containerRef.current || mapRef.current) return;

    const maplibregl = (await import("maplibre-gl")).default;
    // CSS se importa via globals.css (@import "maplibre-gl/dist/maplibre-gl.css")
    const maptilerKey = process.env.NEXT_PUBLIC_MAPTILER_API_KEY;
    const styleUrl = maptilerKey && maptilerKey !== "your-maptiler-api-key-here"
      ? `https://api.maptiler.com/maps/streets-v2/style.json?key=${maptilerKey}`
      : "https://demotiles.maplibre.org/style.json";

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: BARRANQUILLA,
      zoom: 12,
      pitch,
      bearing: 0,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(
      new maplibregl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
      }),
      "top-right"
    );

    map.on("load", () => {
      mapRef.current = map;
      onMapReady?.(map);
    });
  }, [onMapReady, pitch]);

  useEffect(() => {
    initMap();
    return () => {
      if (mapRef.current) {
        (mapRef.current as { remove: () => void }).remove();
        mapRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Actualizar pitch cuando cambia la prop
  useEffect(() => {
    if (mapRef.current) {
      (mapRef.current as { easeTo: (opts: unknown) => void }).easeTo({
        pitch,
        bearing: pitch > 0 ? -17.6 : 0,
        duration: 600,
      });
    }
  }, [pitch]);

  return <div ref={containerRef} className={className} />;
}
