"use client";
import { useState, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { AuditLog } from "@/lib/types";
import { useI18n } from "@/lib/i18n-context";

export default function AuditPage() {
  const { t, formatDate } = useI18n();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadLogs(); }, []);

  const loadLogs = async () => {
    setLoading(true);
    try { setLogs(await api.getAuditLogs()); } catch {}
    setLoading(false);
  };

  const actionBadge = (action: string) => {
    const colors: Record<string, string> = {
      login: "bg-blue-100 text-blue-700",
      create_company: "bg-emerald-100 text-emerald-700",
      create_user: "bg-purple-100 text-purple-700",
      upload_document: "bg-amber-100 text-amber-700",
      create_faq: "bg-orange-100 text-orange-700",
      create_dataset: "bg-cyan-100 text-cyan-700",
      upload_table: "bg-teal-100 text-teal-700",
    };
    const labels: Record<string, string> = {
      login: t("audit.login"),
      create_company: t("audit.createCompany"),
      create_user: t("audit.createUser"),
      upload_document: t("audit.uploadDocument"),
      create_faq: t("audit.createFaq"),
      create_dataset: t("audit.createDataset"),
      upload_table: t("audit.uploadTable"),
    };
    return <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[action] || "bg-slate-100 text-slate-600"}`}>{labels[action] || action.replace(/_/g, " ")}</span>;
  };

  const display = (value?: string | null) => value?.trim() || "—";
  const resourceKind = (value?: string | null) => {
    const key = value?.trim().toLowerCase();
    return ({
      document: t("audit.document"),
      faq: t("audit.faq"),
      dataset: t("audit.dataset"),
      organization: t("audit.organizationType"),
      company: t("audit.organizationType"),
      user: t("audit.userType"),
    } as Record<string, string>)[key || ""] || display(value);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-900">{t("audit.title")}</h1><p className="text-slate-500 mt-1">{t("audit.copy")}</p></div>
        <button onClick={loadLogs} disabled={loading} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 text-sm text-slate-600 hover:bg-slate-50">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> {t("common.refresh")}
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200"><tr>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("audit.time")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("audit.action")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("audit.user")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("audit.organization")}</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("audit.resource")}</th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {logs.map(log => (
              <tr key={log.id} className="hover:bg-slate-50">
                <td className="px-6 py-4 text-sm text-slate-500">{formatDate(log.created_at, { dateStyle: "medium", timeStyle: "short" })}</td>
                <td className="px-6 py-4">{actionBadge(log.action)}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{display(log.actor_label || log.user_name || log.user_email)}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{display(log.organization_name || log.company_name)}</td>
                <td className="px-6 py-4 text-sm text-slate-600">
                  <div className="font-medium text-slate-700">{display(log.resource_label)}</div>
                  {log.resource_kind_label && <div className="mt-0.5 text-xs text-slate-400">{resourceKind(log.resource_kind_label)}</div>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 && <div className="text-center py-12 text-slate-400">{t("audit.empty")}</div>}
      </div>
    </div>
  );
}
