"use client";

import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, MapPin } from "lucide-react";
import { api } from "@/lib/api";
import type { Stop } from "@/lib/types";

function getToken() {
  return typeof window !== "undefined" ? localStorage.getItem("admin_token") ?? "" : "";
}

interface StopFormData {
  name: string;
  lat: string;
  lon: string;
  code: string;
}

export default function AdminStopsPage() {
  const [stops, setStops] = useState<Stop[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editStop, setEditStop] = useState<Stop | null>(null);
  const [form, setForm] = useState<StopFormData>({ name: "", lat: "", lon: "", code: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const load = (q?: string) =>
    api.stops(q).then(setStops).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditStop(null);
    setForm({ name: "", lat: "", lon: "", code: "" });
    setError("");
    setShowForm(true);
  };

  const openEdit = (s: Stop) => {
    setEditStop(s);
    setForm({ name: s.name, lat: s.lat?.toString() ?? "", lon: s.lon?.toString() ?? "", code: s.code ?? "" });
    setError("");
    setShowForm(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    const token = getToken();
    const body = {
      name: form.name.trim(),
      lat: form.lat ? parseFloat(form.lat) : null,
      lon: form.lon ? parseFloat(form.lon) : null,
      code: form.code.trim() || null,
    };
    try {
      if (editStop) {
        await api.updateStop(editStop.id, body, token);
      } else {
        await api.createStop(body, token);
      }
      setShowForm(false);
      load(search || undefined);
    } catch (err: unknown) {
      setError((err as Error).message || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (s: Stop) => {
    if (!confirm(`¿Eliminar el paradero "${s.name}"?`)) return;
    await api.deleteStop(s.id, getToken()).catch(() => null);
    load(search || undefined);
  };

  const handleSearch = (q: string) => {
    setSearch(q);
    load(q || undefined);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Paraderos</h1>
          <p className="text-slate-400 text-sm">{stops.length} paraderos</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" /> Nuevo paradero
        </button>
      </div>

      {/* Buscador */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Buscar paradero..."
          value={search}
          onChange={(e) => handleSearch(e.target.value)}
          className="w-full max-w-xs bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 outline-none"
        />
      </div>

      {/* Modal form */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md">
            <h2 className="text-white font-semibold mb-4">
              {editStop ? "Editar paradero" : "Nuevo paradero"}
            </h2>
            <form onSubmit={handleSave} className="flex flex-col gap-4">
              <div>
                <label className="text-slate-400 text-xs mb-1 block">Nombre *</label>
                <input type="text" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 outline-none" required />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 text-xs mb-1 block">Latitud</label>
                  <input type="number" step="any" value={form.lat} onChange={(e) => setForm((f) => ({ ...f, lat: e.target.value }))}
                    placeholder="10.9878" className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 outline-none" />
                </div>
                <div>
                  <label className="text-slate-400 text-xs mb-1 block">Longitud</label>
                  <input type="number" step="any" value={form.lon} onChange={(e) => setForm((f) => ({ ...f, lon: e.target.value }))}
                    placeholder="-74.7964" className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 outline-none" />
                </div>
              </div>
              <div>
                <label className="text-slate-400 text-xs mb-1 block">Código</label>
                <input type="text" value={form.code} onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
                  className="w-full bg-slate-800 text-white text-sm rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 outline-none" />
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
                <th className="text-left px-5 py-3 text-slate-400 font-medium">Coordenadas</th>
                <th className="text-left px-5 py-3 text-slate-400 font-medium">Código</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {stops.map((s) => (
                <tr key={s.id} className="hover:bg-slate-800/50 transition-colors">
                  <td className="px-5 py-3 text-white max-w-xs truncate">{s.name}</td>
                  <td className="px-5 py-3">
                    {s.lat && s.lon ? (
                      <span className="flex items-center gap-1 text-green-400 text-xs">
                        <MapPin className="w-3 h-3" />
                        {s.lat.toFixed(4)}, {s.lon.toFixed(4)}
                      </span>
                    ) : (
                      <span className="text-slate-600 text-xs italic">Sin coordenadas</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-slate-400 font-mono">{s.code ?? "—"}</td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => openEdit(s)} className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(s)} className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors">
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
