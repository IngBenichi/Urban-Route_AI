"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Route } from "@/lib/types";

function getToken() {
  return typeof window !== "undefined" ? localStorage.getItem("admin_token") ?? "" : "";
}

interface RouteFormData {
  name: string;
  code: string;
  color: string;
}

const COLORS = ["#3B82F6","#EF4444","#10B981","#F59E0B","#8B5CF6","#EC4899","#14B8A6","#F97316"];

export default function AdminRoutesPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editRoute, setEditRoute] = useState<Route | null>(null);
  const [form, setForm] = useState<RouteFormData>({ name: "", code: "", color: "#3B82F6" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = () => api.routes().then(setRoutes).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditRoute(null);
    setForm({ name: "", code: "", color: "#3B82F6" });
    setError("");
    setShowForm(true);
  };

  const openEdit = (r: Route) => {
    setEditRoute(r);
    setForm({ name: r.name, code: r.code ?? "", color: r.color });
    setError("");
    setShowForm(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    const token = getToken();
    const body = { name: form.name.trim(), code: form.code.trim() || undefined, color: form.color };
    try {
      if (editRoute) {
        await api.updateRoute(editRoute.id, body, token);
      } else {
        await api.createRoute(body, token);
      }
      setShowForm(false);
      load();
    } catch (err: unknown) {
      setError((err as Error).message || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (r: Route) => {
    if (!confirm(`¿Eliminar la ruta "${r.name}"?`)) return;
    await api.deleteRoute(r.id, getToken()).catch(() => null);
    load();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Rutas</h1>
          <p className="text-slate-400 text-sm">{routes.length} rutas registradas</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" /> Nueva ruta
        </button>
      </div>

      {/* Modal form */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md">
            <h2 className="text-white font-semibold mb-4">
              {editRoute ? "Editar ruta" : "Nueva ruta"}
            </h2>
            <form onSubmit={handleSave} className="flex flex-col gap-4">
              <div>
                <label className="text-slate-400 text-xs mb-1 block">Nombre *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 outline-none"
                  required
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-1 block">Código</label>
                <input
                  type="text"
                  value={form.code}
                  onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
                  className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-2 block">Color</label>
                <div className="flex gap-2 flex-wrap">
                  {COLORS.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setForm((f) => ({ ...f, color: c }))}
                      className="w-7 h-7 rounded-full border-2 transition-all"
                      style={{
                        backgroundColor: c,
                        borderColor: form.color === c ? "white" : "transparent",
                      }}
                    />
                  ))}
                </div>
              </div>
              {error && <p className="text-red-400 text-xs">{error}</p>}
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowForm(false)} className="text-slate-400 hover:text-white text-sm px-4 py-2 transition-colors">
                  Cancelar
                </button>
                <button type="submit" disabled={saving} className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
                  {saving ? "Guardando..." : "Guardar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Tabla */}
      {loading ? (
        <p className="text-slate-400 text-sm">Cargando...</p>
      ) : (
        <div className="bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-700">
              <tr>
                <th className="text-left px-5 py-3 text-slate-400 font-medium">Nombre</th>
                <th className="text-left px-5 py-3 text-slate-400 font-medium">Código</th>
                <th className="text-left px-5 py-3 text-slate-400 font-medium">Color</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {routes.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/50 transition-colors">
                  <td className="px-5 py-3 text-white">{r.name}</td>
                  <td className="px-5 py-3 text-slate-400 font-mono">{r.code ?? "—"}</td>
                  <td className="px-5 py-3">
                    <span className="inline-flex items-center gap-2">
                      <span className="w-4 h-4 rounded-full" style={{ backgroundColor: r.color }} />
                      <span className="text-slate-400 font-mono text-xs">{r.color}</span>
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => openEdit(r)} className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(r)} className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
