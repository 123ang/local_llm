"use client";
import { useState, useEffect } from "react";
import { Building2, Plus, X, ToggleLeft, ToggleRight } from "lucide-react";
import { api } from "@/lib/api";

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadCompanies(); }, []);

  const loadCompanies = async () => {
    try { setCompanies(await api.getCompanies()); } catch {}
  };

  const handleCreate = async () => {
    if (!name) return;
    setLoading(true);
    try {
      await api.createCompany({ name, description: description || undefined });
      await loadCompanies();
      setShowForm(false); setName(""); setDescription("");
    } catch {}
    setLoading(false);
  };

  const toggleActive = async (company: any) => {
    try {
      await api.updateCompany(company.id, { is_active: !company.is_active });
      await loadCompanies();
    } catch {}
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-900">Companies</h1><p className="text-slate-500 mt-1">Manage company tenants</p></div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors"><Plus size={16} /> Add Company</button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4"><h2 className="text-lg font-semibold">New Company</h2><button onClick={() => setShowForm(false)} className="text-slate-400"><X size={20} /></button></div>
          <div className="flex gap-4 items-end">
            <div className="flex-1"><label className="block text-sm font-medium text-slate-700 mb-1">Name</label><input value={name} onChange={e => setName(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <div className="flex-1"><label className="block text-sm font-medium text-slate-700 mb-1">Description</label><input value={description} onChange={e => setDescription(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <button onClick={handleCreate} disabled={loading || !name} className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50">{loading ? "Creating..." : "Create"}</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200"><tr>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Company</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Slug</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Created</th>
            <th className="px-6 py-3"></th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {companies.map(c => (
              <tr key={c.id} className="hover:bg-slate-50">
                <td className="px-6 py-4 flex items-center gap-3"><Building2 size={18} className="text-red-500" /><span className="text-sm font-medium text-slate-900">{c.name}</span></td>
                <td className="px-6 py-4 text-sm text-slate-500">{c.slug}</td>
                <td className="px-6 py-4"><span className={`px-2 py-1 text-xs font-medium rounded-full ${c.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{c.is_active ? "Active" : "Inactive"}</span></td>
                <td className="px-6 py-4 text-sm text-slate-500">{new Date(c.created_at).toLocaleDateString()}</td>
                <td className="px-6 py-4"><button onClick={() => toggleActive(c)} className="text-slate-400 hover:text-slate-600">{c.is_active ? <ToggleRight size={20} className="text-emerald-500" /> : <ToggleLeft size={20} />}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {companies.length === 0 && <div className="text-center py-12 text-slate-400">No companies yet</div>}
      </div>
    </div>
  );
}
