"use client";
import { Fragment, useState, useEffect } from "react";
import { Building2, Plus, X, ToggleLeft, ToggleRight, Settings, Save } from "lucide-react";
import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n-context";

const SOURCE_OPTIONS = ["database", "documents", "faq", "apis"];

export default function CompaniesPage() {
  const { t, formatDate } = useI18n();
  const sourceLabel = (source: string) => ({
    database: t("assistant.sourceDatabase"),
    documents: t("assistant.sourceDocuments"),
    faq: t("assistant.sourceFaq"),
    apis: t("assistant.apis"),
  }[source] || source);
  const [companies, setCompanies] = useState<any[]>([]);
  const [departmentsByCompany, setDepartmentsByCompany] = useState<Record<number, any[]>>({});
  const [showForm, setShowForm] = useState(false);
  const [departmentForm, setDepartmentForm] = useState<{ company_id: number | null; name: string; description: string }>({ company_id: null, name: "", description: "" });
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [settingsCompany, setSettingsCompany] = useState<any | null>(null);
  const [aiSettings, setAiSettings] = useState<any | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);

  useEffect(() => { loadCompanies(); }, []);

  const loadCompanies = async () => {
    try {
      const items = await api.getCompanies();
      setCompanies(items);
      const pairs = await Promise.all(items.map(async (company: any) => {
        try {
          return [company.id, await api.getDepartments(company.id)] as const;
        } catch {
          return [company.id, []] as const;
        }
      }));
      setDepartmentsByCompany(Object.fromEntries(pairs));
    } catch {}
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

  const createDepartment = async () => {
    if (!departmentForm.company_id || !departmentForm.name) return;
    try {
      await api.createDepartment({
        company_id: departmentForm.company_id,
        name: departmentForm.name,
        description: departmentForm.description || undefined,
      });
      setDepartmentForm({ company_id: null, name: "", description: "" });
      await loadCompanies();
    } catch {}
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-900">{t("organizations.title")}</h1><p className="text-slate-500 mt-1">{t("organizations.copy")}</p></div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors"><Plus size={16} /> {t("organizations.add")}</button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4"><h2 className="text-lg font-semibold">{t("organizations.new")}</h2><button onClick={() => setShowForm(false)} title={t("common.close")} className="text-slate-400"><X size={20} /></button></div>
          <div className="flex gap-4 items-end">
            <div className="flex-1"><label className="block text-sm font-medium text-slate-700 mb-1">{t("organizations.name")}</label><input value={name} onChange={e => setName(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <div className="flex-1"><label className="block text-sm font-medium text-slate-700 mb-1">{t("organizations.description")}</label><input value={description} onChange={e => setDescription(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" /></div>
            <button onClick={handleCreate} disabled={loading || !name} className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50">{loading ? t("organizations.creating") : t("organizations.create")}</button>
          </div>
        </div>
      )}

      {settingsCompany && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">{t("organizations.knowledgeSettings", { name: settingsCompany.name })}</h2>
              <p className="text-sm text-slate-500">{t("organizations.settingsCopy")}</p>
            </div>
            <button onClick={() => setSettingsCompany(null)} className="text-slate-400"><X size={20} /></button>
          </div>

          {!aiSettings ? <div className="text-sm text-slate-400">{t("organizations.loadingSettings")}</div> : (
            <div className="grid md:grid-cols-2 gap-4">
              <label className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                <span><span className="font-medium text-slate-700">{t("organizations.sourceOnlyDefault")}</span><br /><span className="text-xs text-slate-400">{t("organizations.sourceOnlyDefaultCopy")}</span></span>
                <input type="checkbox" checked={aiSettings.default_source_only} onChange={e => setAiSettings({ ...aiSettings, default_source_only: e.target.checked })} />
              </label>
              <label className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                <span><span className="font-medium text-slate-700">{t("organizations.allowInsights")}</span><br /><span className="text-xs text-slate-400">{t("organizations.allowInsightsCopy")}</span></span>
                <input type="checkbox" checked={aiSettings.ai_insights_allowed} onChange={e => setAiSettings({ ...aiSettings, ai_insights_allowed: e.target.checked })} />
              </label>
              <label className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                <span><span className="font-medium text-slate-700">{t("organizations.requireCitations")}</span><br /><span className="text-xs text-slate-400">{t("organizations.requireCitationsCopy")}</span></span>
                <input type="checkbox" checked={aiSettings.require_citations} onChange={e => setAiSettings({ ...aiSettings, require_citations: e.target.checked })} />
              </label>
              <label className="flex items-center justify-between rounded-lg border border-slate-200 p-3 text-sm">
                <span><span className="font-medium text-slate-700">{t("organizations.adminSql")}</span><br /><span className="text-xs text-slate-400">{t("organizations.adminSqlCopy")}</span></span>
                <input type="checkbox" checked={aiSettings.sql_visible_to_admins_only} onChange={e => setAiSettings({ ...aiSettings, sql_visible_to_admins_only: e.target.checked })} />
              </label>
              <div className="rounded-lg border border-slate-200 p-3 text-sm">
                <div className="font-medium text-slate-700 mb-2">{t("organizations.allowedSources")}</div>
                <div className="flex flex-wrap gap-2">
                  {SOURCE_OPTIONS.map(source => (
                    <button key={source} type="button" onClick={() => toggleAllowedSource(source)} className={`px-2.5 py-1.5 rounded-lg border text-xs font-medium ${aiSettings.allowed_sources?.includes(source) ? "bg-red-50 border-red-300 text-red-700" : "bg-white border-slate-200 text-slate-400"}`}>
                      {sourceLabel(source)}
                    </button>
                  ))}
                </div>
              </div>
              <label className="rounded-lg border border-slate-200 p-3 text-sm">
                <span className="font-medium text-slate-700">{t("organizations.minRelevance")}</span>
                <input type="number" min="0" max="1" step="0.01" value={aiSettings.min_document_relevance} onChange={e => setAiSettings({ ...aiSettings, min_document_relevance: e.target.value })} className="mt-2 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                <span className="text-xs text-slate-400">{t("organizations.minRelevanceCopy")}</span>
              </label>
              <div className="md:col-span-2 flex justify-end">
                <button onClick={saveSettings} disabled={savingSettings} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50">
                  <Save size={15} /> {savingSettings ? t("organizations.saving") : t("organizations.saveSettings")}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200"><tr>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("organizations.organization")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("organizations.slug")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("organizations.status")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("organizations.created")}</th>
            <th className="px-6 py-3"></th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {companies.map(c => (
              <Fragment key={c.id}>
              <tr className="hover:bg-slate-50">
                <td className="px-6 py-4 flex items-center gap-3"><Building2 size={18} className="text-red-500" /><span className="text-sm font-medium text-slate-900">{c.name}</span></td>
                <td className="px-6 py-4 text-sm text-slate-500">{c.slug}</td>
                <td className="px-6 py-4"><span className={`px-2 py-1 text-xs font-medium rounded-full ${c.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>{c.is_active ? t("common.active") : t("common.inactive")}</span></td>
                <td className="px-6 py-4 text-sm text-slate-500">{formatDate(c.created_at)}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => openSettings(c)} className="text-slate-400 hover:text-red-600" title={t("organizations.aiSettings")}><Settings size={18} /></button>
                    <button onClick={() => toggleActive(c)} className="text-slate-400 hover:text-slate-600">{c.is_active ? <ToggleRight size={20} className="text-emerald-500" /> : <ToggleLeft size={20} />}</button>
                  </div>
                </td>
              </tr>
              <tr className="bg-slate-50/60">
                <td colSpan={5} className="px-6 py-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold uppercase text-slate-400">{t("organizations.departments")}</span>
                    {(departmentsByCompany[c.id] || []).map((department) => (
                      <span key={department.id} className="px-2.5 py-1 rounded-full bg-white border border-slate-200 text-xs text-slate-700">
                        {department.name}
                      </span>
                    ))}
                    {departmentForm.company_id === c.id ? (
                      <div className="flex items-center gap-2 ml-2">
                        <input
                          value={departmentForm.name}
                          onChange={(e) => setDepartmentForm({ ...departmentForm, name: e.target.value })}
                          placeholder={t("organizations.departmentName")}
                          className="px-2 py-1 border border-slate-300 rounded-md text-xs"
                        />
                        <input
                          value={departmentForm.description}
                          onChange={(e) => setDepartmentForm({ ...departmentForm, description: e.target.value })}
                          placeholder={t("organizations.description")}
                          className="px-2 py-1 border border-slate-300 rounded-md text-xs"
                        />
                        <button onClick={createDepartment} className="px-2.5 py-1 rounded-md bg-red-600 text-white text-xs font-medium">{t("common.add")}</button>
                        <button onClick={() => setDepartmentForm({ company_id: null, name: "", description: "" })} className="px-2.5 py-1 rounded-md border border-slate-300 text-xs text-slate-600">{t("common.cancel")}</button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDepartmentForm({ company_id: c.id, name: "", description: "" })}
                        className="px-2.5 py-1 rounded-md border border-slate-300 bg-white text-xs font-medium text-slate-600 hover:text-red-600"
                      >
                        + {t("organizations.addDepartment")}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
              </Fragment>
            ))}
          </tbody>
        </table>
        {companies.length === 0 && <div className="text-center py-12 text-slate-400">{t("organizations.empty")}</div>}
      </div>
    </div>
  );
}
