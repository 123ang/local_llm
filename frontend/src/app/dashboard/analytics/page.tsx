"use client";
import { useEffect, useState } from "react";
import { BarChart3, Clock, Database, FileText, HelpCircle, RefreshCw, Users } from "lucide-react";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";
import { useI18n } from "@/lib/i18n-context";

function StatCard({ label, value, icon: Icon }: { label: string; value: string | number; icon: any }) {
  return <div className="bg-white rounded-xl border border-slate-200 p-4"><div className="flex items-center justify-between"><p className="text-xs text-slate-400">{label}</p><Icon size={18} className="text-red-500"/></div><p className="mt-2 text-2xl font-bold text-slate-900">{value}</p></div>;
}

function ListCard({ title, items, empty }: { title: string; items: any[]; empty: string }) {
  return <div className="bg-white rounded-xl border border-slate-200 p-5"><h2 className="font-semibold text-slate-900 mb-3">{title}</h2><div className="space-y-2">{items?.length ? items.map((it, idx) => <div key={idx} className="flex items-center justify-between gap-4 rounded-lg bg-slate-50 px-3 py-2 text-sm"><span className="text-slate-700 truncate">{it.question || it.name}</span><span className="text-xs font-semibold text-slate-500">{it.count}</span></div>) : <p className="text-sm text-slate-400">{empty}</p>}</div></div>;
}

export default function AnalyticsPage() {
  const { t } = useI18n();
  const companyId = useCompanyId();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (!companyId) return;
    setLoading(true);
    try { setData(await api.getAnalyticsSummary(companyId)); } catch { setData(null); }
    setLoading(false);
  };
  useEffect(() => { load(); }, [companyId]);

  const sourceCounts = data?.source_counts || {};
  const maxSource = Math.max(1, ...Object.values(sourceCounts).map((v:any)=>Number(v)||0));

  return <div className="space-y-6">
    <div className="flex items-center justify-between"><div><h1 className="text-2xl font-bold text-slate-900">{t("analytics.title")}</h1><p className="text-slate-500 mt-1">{t("analytics.copy", { days: data?.window_days || 30 })}</p></div><button onClick={load} disabled={loading} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 text-sm text-slate-600 hover:bg-slate-50"><RefreshCw size={14} className={loading ? "animate-spin" : ""}/> {t("common.refresh")}</button></div>

    <div className="grid md:grid-cols-5 gap-4">
      <StatCard label={t("analytics.questions")} value={data?.total_questions ?? 0} icon={BarChart3}/>
      <StatCard label={t("analytics.answers")} value={data?.assistant_answers ?? 0} icon={HelpCircle}/>
      <StatCard label={t("analytics.unanswered")} value={data?.refused_or_unanswered ?? 0} icon={HelpCircle}/>
      <StatCard label={t("analytics.activeUsers")} value={data?.active_users ?? 0} icon={Users}/>
      <StatCard label={t("analytics.avgResponse")} value={data?.average_response_time_ms ? `${(data.average_response_time_ms/1000).toFixed(1)}s` : "—"} icon={Clock}/>
    </div>

    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <h2 className="font-semibold text-slate-900 mb-4">{t("analytics.sourceUsage")}</h2>
      <div className="space-y-3">
        {[{key:"database", icon:Database}, {key:"documents", icon:FileText}, {key:"faq", icon:HelpCircle}].map(({key, icon:Icon}) => {
          const count = sourceCounts[key] || 0;
          return <div key={key}><div className="flex items-center justify-between text-sm mb-1"><span className="inline-flex items-center gap-2 text-slate-700"><Icon size={14}/>{t(`analytics.${key}`)}</span><span className="text-slate-500">{count}</span></div><div className="h-2 rounded-full bg-slate-100 overflow-hidden"><div className="h-full bg-red-500" style={{ width: `${Math.round(count / maxSource * 100)}%` }} /></div></div>;
        })}
      </div>
    </div>

    <div className="grid lg:grid-cols-3 gap-4">
      <ListCard title={t("analytics.mostAsked")} items={data?.top_questions || []} empty={t("analytics.noRepeated")} />
      <ListCard title={t("analytics.mostDocuments")} items={data?.top_documents || []} empty={t("analytics.noDocuments")} />
      <ListCard title={t("analytics.mostDatasets")} items={data?.top_datasets || []} empty={t("analytics.noDatasets")} />
    </div>
  </div>;
}
