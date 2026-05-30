"use client";

import { useState, useEffect, ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { Bus, MapPin, LayoutDashboard, LogOut } from "lucide-react";

function isTokenValid(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

function LoginForm({ onLogin }: { onLogin: (token: string) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) { setError("Credenciales incorrectas."); return; }
      const data = await res.json();
      localStorage.setItem("admin_token", data.access_token);
      onLogin(data.access_token);
    } catch {
      setError("Error de conexión con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-slate-900 border border-slate-700 rounded-2xl p-8">
        <h1 className="text-white text-xl font-bold mb-1">Panel de Administración</h1>
        <p className="text-slate-400 text-sm mb-6">Ingresa tus credenciales de administrador</p>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Usuario"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="bg-slate-800 text-white text-sm rounded-lg px-3 py-2.5 border border-slate-600 focus:border-blue-500 outline-none"
            required
          />
          <input
            type="password"
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="bg-slate-800 text-white text-sm rounded-lg px-3 py-2.5 border border-slate-600 focus:border-blue-500 outline-none"
            required
          />
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-sm rounded-lg py-2.5 transition-colors"
          >
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AdminLayout({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [checked, setChecked] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const stored = localStorage.getItem("admin_token");
    if (stored && isTokenValid(stored)) setToken(stored);
    setChecked(true);
  }, []);

  const logout = () => {
    localStorage.removeItem("admin_token");
    setToken(null);
  };

  if (!checked) return null;
  if (!token) return <LoginForm onLogin={setToken} />;

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)]">
      {/* Sidebar admin */}
      <aside className="w-56 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <p className="text-slate-400 text-xs uppercase tracking-wider font-semibold">Admin Panel</p>
        </div>
        <nav className="flex-1 p-3 flex flex-col gap-1">
          <Link href="/admin" className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${pathname === "/admin" ? "bg-blue-600 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"}`}>
            <LayoutDashboard className="w-4 h-4" /> Dashboard
          </Link>
          <Link href="/admin/routes" className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${pathname.startsWith("/admin/routes") ? "bg-blue-600 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"}`}>
            <Bus className="w-4 h-4" /> Rutas
          </Link>
          <Link href="/admin/stops" className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${pathname.startsWith("/admin/stops") ? "bg-blue-600 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"}`}>
            <MapPin className="w-4 h-4" /> Paraderos
          </Link>
        </nav>
        <div className="p-3 border-t border-slate-800">
          <button onClick={logout} className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-red-900/20 transition-colors">
            <LogOut className="w-4 h-4" /> Cerrar sesión
          </button>
        </div>
      </aside>

      {/* Contenido */}
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  );
}
