import type { Metadata } from "next";
import localFont from "next/font/local";
import Link from "next/link";
import { Bus, Map, Settings } from "lucide-react";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Urban Route AI — Rutas de Buses Barranquilla",
  description: "Sistema inteligente de rutas de buses de Barranquilla con IA y mapas 2D/3D",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className={`${geistSans.variable} font-sans bg-slate-950 text-white antialiased min-h-screen`}>
        {/* Navbar */}
        <header className="fixed top-0 left-0 right-0 z-40 bg-slate-950/90 backdrop-blur border-b border-slate-800">
          <nav className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-bold text-white">
              <div className="bg-blue-600 p-1.5 rounded-lg">
                <Bus className="w-4 h-4" />
              </div>
              <span className="text-sm tracking-tight">
                Urban<span className="text-blue-400">Route</span>{" "}
                <span className="text-slate-400 font-normal">AI</span>
              </span>
            </Link>
            <div className="flex items-center gap-1">
              <Link href="/" className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                <Bus className="w-4 h-4" /> Inicio
              </Link>
              <Link href="/map" className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                <Map className="w-4 h-4" /> Mapa
              </Link>
              <Link href="/admin" className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors">
                <Settings className="w-4 h-4" /> Admin
              </Link>
            </div>
          </nav>
        </header>
        <main className="pt-14">{children}</main>
      </body>
    </html>
  );
}
