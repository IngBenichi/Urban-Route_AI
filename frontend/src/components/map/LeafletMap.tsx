"use client";

import { useEffect, useRef } from "react";

const BARRANQUILLA: [number, number] = [10.9878, -74.7964];

interface LeafletMapProps {
  onMapReady?: (map: unknown) => void;
  onLocationUpdate?: (lat: number, lon: number) => void;
  className?: string;
}

export default function LeafletMap({ onMapReady, onLocationUpdate, className = "" }: LeafletMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<unknown>(null);
  const userMarkerRef = useRef<unknown>(null);
  const watchIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    let map: import("leaflet").Map;

    const initMap = async () => {
      if (!containerRef.current) return;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if ((containerRef.current as any)._leaflet_id) return;

      const L = (await import("leaflet")).default;

      // Fix íconos rotos en Next.js
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
        iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
        shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
      });

      map = L.map(containerRef.current!, {
        center: BARRANQUILLA,
        zoom: 12,
        zoomControl: true,
      });

      L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20,
      }).addTo(map);

      // Ícono personalizado de ubicación del usuario (punto azul pulsante)
      const userIcon = L.divIcon({
        className: "",
        html: `<div style="
          width:16px;height:16px;border-radius:50%;
          background:#3B82F6;border:3px solid #fff;
          box-shadow:0 0 0 4px rgba(59,130,246,0.3);
          animation:pulse-blue 2s infinite;
        "></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });

      // Inyectar animación CSS si no existe
      if (!document.getElementById("leaflet-pulse-style")) {
        const style = document.createElement("style");
        style.id = "leaflet-pulse-style";
        style.textContent = `
          @keyframes pulse-blue {
            0%   { box-shadow: 0 0 0 0 rgba(59,130,246,0.5); }
            70%  { box-shadow: 0 0 0 10px rgba(59,130,246,0); }
            100% { box-shadow: 0 0 0 0 rgba(59,130,246,0); }
          }
        `;
        document.head.appendChild(style);
      }

      // Geolocalización continua
      if (navigator.geolocation) {
        watchIdRef.current = navigator.geolocation.watchPosition(
          (pos) => {
            const { latitude: lat, longitude: lon } = pos.coords;
            if (userMarkerRef.current) {
              (userMarkerRef.current as import("leaflet").Marker).setLatLng([lat, lon]);
            } else {
              userMarkerRef.current = L.marker([lat, lon], { icon: userIcon, zIndexOffset: 1000 })
                .bindPopup("📍 Tu ubicación actual")
                .addTo(map);
              map.flyTo([lat, lon], 14, { duration: 1.5 });
            }
            onLocationUpdate?.(lat, lon);
          },
          () => { /* permiso denegado o error — no hacer nada */ },
          { enableHighAccuracy: true, maximumAge: 5000 }
        );
      }

      mapRef.current = map;
      onMapReady?.(map);
    };

    initMap();

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
      if (mapRef.current) {
        (mapRef.current as import("leaflet").Map).remove();
        mapRef.current = null;
        userMarkerRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <div ref={containerRef} className={className} />;
}

