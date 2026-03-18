"use client";
import { useState, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { api } from "@/lib/api";

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
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
    return <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[action] || "bg-slate-100 text-slate-600"}`}>{action.replace(/_/g, " ")}</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-slate-900">Audit Logs</h1><p className="text-slate-500 mt-1">Track platform activity</p></div>
        <button onClick={loadLogs} disabled={loading} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-300 text-sm text-slate-600 hover:bg-slate-50">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200"><tr>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Time</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Action</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Resource</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">User ID</th>
            <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Company ID</th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">
            {logs.map(log => (
              <tr key={log.id} className="hover:bg-slate-50">
                <td className="px-6 py-4 text-sm text-slate-500">{new Date(log.created_at).toLocaleString()}</td>
                <td className="px-6 py-4">{actionBadge(log.action)}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{log.resource_type ? `${log.resource_type} #${log.resource_id}` : "—"}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{log.user_id || "—"}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{log.company_id || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 && <div className="text-center py-12 text-slate-400">No audit logs yet</div>}
      </div>
    </div>
  );
}
