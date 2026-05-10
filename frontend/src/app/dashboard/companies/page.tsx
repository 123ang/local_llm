"use client";
import { useState, useEffect } from "react";
import { Building2, Plus, X, ToggleLeft, ToggleRight, Settings, Save } from "lucide-react";
import { api } from "@/lib/api";

const SOURCE_OPTIONS = ["database", "documents", "faq"];

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [settingsCompany, setSettingsCompany] = useState<any | null>(null);
  const [aiSettings, setAiSettings] = useState<any | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);

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

  const openSettings = async (company: any) => {
    setSettingsCompany(company);
    setAiSettings(null);
    try {
      setAiSettings(await api.getCompanyAISettings(company.id));
    } catch {}
  };

  const saveSettings = async () => {
    if (!settingsCompany || !aiSettings) return;
    setSavingSettings(true);
    try {
      const saved = await api.updateCompanyAISettings(settingsCompany.id, {
        default_source_only: aiSettings.default_source_only,
        ai_insights_allowed: aiSettings.ai_insights_allowed,
        allowed_sources: aiSettings.allowed_sources,
        min_document_relevance: Number(aiSettings.min_document_relevance),
        require_citations: aiSettings.require_citations,
        sql_visible_to_admins_only: aiSettings.sql_visible_to_admins_only,
      });
      setAiSettings(saved);
    } catch {}
    setSavingSettings(false);
  };

  const toggleAllowedSource = (source: string) => {
    setAiSettings((prev: any) => {
      if (!prev) return prev;
      const set = new Set(prev.allowed_sources || []);
      if (set.has(source)) {
        if (set.size > 1) set.delete(source);
      } else {
        set.add(source);
      }
      return { ...prev, allowed_sources: Array.from(set) };
    });
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

      {settingsCompany && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">AI Settings — {settingsCompany.name}</h2>
              <p className="text-sm text-slate-500">Super admin only. These settings control source-only behavior and evidence requirements.</p>
            </div>
            <button onClick={() => setSettingsCompany(null)} className="text-slate-400"><X size={20} /></button>
          </div>

          {!aiSettings ? <div className="text-sm text-slate-400">Loading settings...</div> : (
            <div className="grid md:grid-cols-2 gap-4">
              <label className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                <span><span className="font-medium text-slate-700">Source Only by default</span><br /><span className="text-xs text-slate-400">No general AI unless AI Insights is enabled.</span></span>
                <input type="checkbox" checked={aiSettings.default_source_only} onChange={e => setAiSettings({ ...aiSettings, default_source_only: e.target.checked })} />
              </label>
              <label className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                <span><span className="font-medium text-slate-700">Allow AI Insights</span><br /><span className="text-xs text-slate-400">If off, users cannot use general fallback.</span></span>
                <input type="checkbox" checked={aiSettings.ai_insights_allowed} onChange={e => setAiSettings({ ...aiSettings, ai_insights_allowed: e.target.checked })} />
              </label>
              <label className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                <span><span className="font-medium text-slate-700">Require citations</span><br /><span className="text-xs text-slate-400">Answers should cite PDF/page or dataset.</span></span>
                <input type="checkbox" checked={aiSettings.require_citations} onChange={e => setAiSettings({ ...aiSettings, require_citations: e.target.checked })} />
              </label>
              <label className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                <span><span className="font-medium text-slate-700">SQL visible to admins only</span><br /><span className="text-xs text-slate-400">Normal users cannot see generated SQL.</span></span>
                <input type="checkbox" checked={aiSettings.sql_visible_to_admins_only} onChange={e => setAiSettings({ ...aiSettings, sql_visible_to_admins_only: e.target.checked })} />
              </label>
              <div className="rounded-lg border border-slate-200 p-3 text-sm">
                <div className="font-medium text-slate-700 mb-2">Allowed sources</div>
                <div className="flex flex-wrap gap-2">
                  {SOURCE_OPTIONS.map(source => (
                    <button key={source} type="button" onClick={() => toggleAllowedSource(source)} className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium ${aiSettings.allowed_sources?.includes(source) ? "bg-red-50 border-red-300 text-red-700" : "bg-white border-slate-200 text-slate-400"}`}>
                      {source}
                    </button>
                  ))}
                </div>
              </div>
              <label className="rounded-lg border border-slate-200 p-3 text-sm">
                <span className="font-medium text-slate-700">Minimum PDF relevance</span>
                <input type="number" min="0" max="1" step="0.01" value={aiSettings.min_document_relevance} onChange={e => setAiSettings({ ...aiSettings, min_document_relevance: e.target.value })} className="mt-2 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                <span className="text-xs text-slate-400">Recommended: 0.60 for Source Only mode.</span>
              </label>
              <div className="md:col-span-2 flex justify-end">
                <button onClick={saveSettings} disabled={savingSettings} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50">
                  <Save size={15} /> {savingSettings ? "Saving..." : "Save AI Settings"}
                </button>
              </div>
            </div>
          )}
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
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openSettings(c)} className="text-slate-400 hover:text-red-600" title="AI settings"><Settings size={18} /></button>
                    <button onClick={() => toggleActive(c)} className="text-slate-400 hover:text-slate-600">{c.is_active ? <ToggleRight size={20} className="text-emerald-500" /> : <ToggleLeft size={20} />}</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {companies.length === 0 && <div className="text-center py-12 text-slate-400">No companies yet</div>}
      </div>
    </div>
  );
}
