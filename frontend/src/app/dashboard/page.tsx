"use client";
import { useState, useEffect, useCallback } from "react";
import { FileText, MessageSquare, Database, HelpCircle, TrendingUp, RefreshCw } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";
import { canAccessDashboardPath } from "@/lib/navigation-policy";
import Link from "next/link";

interface SystemStatus {
  ollama: { connected: boolean };
  gpu: { available: boolean; provider: string; memory_used_mb: number | null; memory_total_mb: number | null };
  rag: { connected: boolean };
  database: { connected: boolean; version: string };
  redis: { connected: boolean };
}

export default function OverviewPage() {
  const { user, isSuperAdmin } = useAuth();
  const companyId = useCompanyId();

  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [counts, setCounts] = useState({ documents: 0, faq: 0, datasets: 0, sessions: 0 });

  const loadStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const data = await api.request<SystemStatus>("/status");
      setStatus(data);
    } catch {
      setStatus(null);
    }
    setStatusLoading(false);
  }, []);

  const loadCounts = useCallback(async () => {
    if (!companyId) return;
    try {
      const [docs, faqs, datasets, sessions] = await Promise.allSettled([
        api.getDocuments(companyId),
        api.getFAQ(companyId),
        api.getDatasets(companyId),
        api.getChatSessions(),
      ]);
      setCounts({
        documents: docs.status === "fulfilled" ? docs.value.length : 0,
        faq: faqs.status === "fulfilled" ? faqs.value.length : 0,
        datasets: datasets.status === "fulfilled" ? datasets.value.length : 0,
        sessions: sessions.status === "fulfilled" ? sessions.value.length : 0,
      });
    } catch {}
  }, [companyId]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  useEffect(() => {
    loadCounts();
  }, [loadCounts]);

  const stats = [
    { label: "Documents", value: counts.documents, icon: FileText, color: "text-blue-600", bg: "bg-blue-50", href: "/dashboard/documents" },
    { label: "FAQ Items", value: counts.faq, icon: HelpCircle, color: "text-amber-600", bg: "bg-amber-50", href: "/dashboard/faq" },
    { label: "Datasets", value: counts.datasets, icon: Database, color: "text-emerald-600", bg: "bg-emerald-50", href: "/dashboard/database" },
    { label: "Chat Sessions", value: counts.sessions, icon: MessageSquare, color: "text-purple-600", bg: "bg-purple-50", href: "/dashboard/assistant" },
  ];

  const StatusDot = ({ ok, loading }: { ok: boolean; loading?: boolean }) => {
    if (loading) return <span className="w-2 h-2 rounded-full bg-slate-300 animate-pulse inline-block" />;
    return <span className={`w-2 h-2 rounded-full inline-block ${ok ? "bg-emerald-500" : "bg-red-400"}`} />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Welcome back, {user?.full_name}</h1>
        <p className="text-slate-500 mt-1">Here&apos;s an overview of your knowledge platform</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const card = (
            <>
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2.5 rounded-lg ${stat.bg}`}>
                  <stat.icon size={20} className={stat.color} />
                </div>
                <TrendingUp size={16} className="text-emerald-500" />
              </div>
              <p className="text-2xl font-bold text-slate-900">{companyId ? stat.value : "—"}</p>
              <p className="text-sm text-slate-500 mt-1">{stat.label}</p>
            </>
          );
          if (canAccessDashboardPath(user?.role, stat.href)) {
            return (
              <Link key={stat.label} href={stat.href}
                className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition-shadow block">
                {card}
              </Link>
            );
          }
          return (
            <div key={stat.label} className="bg-white rounded-xl border border-slate-200 p-5">
              {card}
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Start */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            {isSuperAdmin ? "Platform Management" : "Quick Start"}
          </h2>
          <div className="space-y-3">
            {isSuperAdmin ? (
              <>
                <Link href="/dashboard/companies"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition-colors">
                  <div className="p-2 rounded-lg bg-red-50"><Database size={18} className="text-red-600" /></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Manage Organizations</p>
                    <p className="text-xs text-slate-500">Set up departments, tenants, and AI source rules</p>
                  </div>
                </Link>
                <Link href="/dashboard/users"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition-colors">
                  <div className="p-2 rounded-lg bg-blue-50"><MessageSquare size={18} className="text-blue-600" /></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Assign Users</p>
                    <p className="text-xs text-slate-500">Place users into the correct organization</p>
                  </div>
                </Link>
              </>
            ) : (
              <>
                <Link href="/dashboard/assistant"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition-colors">
                  <div className="p-2 rounded-lg bg-red-50"><MessageSquare size={18} className="text-red-600" /></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Ask a Question</p>
                    <p className="text-xs text-slate-500">Chat with your knowledge base</p>
                  </div>
                </Link>
                <Link href="/dashboard/documents"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition-colors">
                  <div className="p-2 rounded-lg bg-blue-50"><FileText size={18} className="text-blue-600" /></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Upload Document</p>
                    <p className="text-xs text-slate-500">Add PDFs to your knowledge base</p>
                  </div>
                </Link>
                <Link href="/dashboard/database"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition-colors">
                  <div className="p-2 rounded-lg bg-emerald-50"><Database size={18} className="text-emerald-600" /></div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">Import Data</p>
                    <p className="text-xs text-slate-500">Upload CSV or create tables</p>
                  </div>
                </Link>
              </>
            )}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">System Status</h2>
            <button onClick={loadStatus} disabled={statusLoading}
              className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50 transition-colors">
              <RefreshCw size={15} className={statusLoading ? "animate-spin" : ""} />
            </button>
          </div>
          <div className="space-y-4">
            {/* Backend */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Backend API</span>
              <span className="flex items-center gap-1.5 text-sm text-emerald-600">
                <StatusDot ok={true} /> Online
              </span>
            </div>

            {/* AI engine */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">AI Engine</span>
              {statusLoading ? (
                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                  <StatusDot ok={false} loading /> Checking…
                </span>
              ) : status?.ollama.connected ? (
                <div className="flex flex-col items-end gap-0.5">
                  <span className="flex items-center gap-1.5 text-sm text-emerald-600">
                    <StatusDot ok={true} /> Connected
                  </span>
                  <span className="text-xs text-slate-400">LLM ready</span>
                </div>
              ) : (
                <div className="flex flex-col items-end gap-0.5">
                  <span className="flex items-center gap-1.5 text-sm text-red-500">
                    <StatusDot ok={false} /> Not connected
                  </span>
                  <span className="text-xs text-slate-400">Service unavailable</span>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Embedding Service</span>
              {statusLoading ? (
                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                  <StatusDot ok={false} loading /> Checking…
                </span>
              ) : (
                <span className={`flex items-center gap-1.5 text-sm ${status?.ollama.connected ? "text-emerald-600" : "text-red-500"}`}>
                  <StatusDot ok={status?.ollama.connected ?? false} />
                  {status?.ollama.connected ? "Connected" : "Not connected"}
                </span>
              )}
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">RAG Service</span>
              {statusLoading ? (
                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                  <StatusDot ok={false} loading /> Checking…
                </span>
              ) : (
                <span className={`flex items-center gap-1.5 text-sm ${status?.rag.connected ? "text-emerald-600" : "text-red-500"}`}>
                  <StatusDot ok={status?.rag.connected ?? false} />
                  {status?.rag.connected ? "Running" : "Not connected"}
                </span>
              )}
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">GPU RAM</span>
              {statusLoading ? (
                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                  <StatusDot ok={false} loading /> Checking…
                </span>
              ) : status?.gpu.available ? (
                <span className="text-sm text-emerald-600">
                  {status.gpu.memory_used_mb} / {status.gpu.memory_total_mb} MB
                </span>
              ) : (
                <span className="text-sm text-slate-400">Unavailable</span>
              )}
            </div>

            {/* Database */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Database</span>
              {statusLoading ? (
                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                  <StatusDot ok={false} loading /> Checking…
                </span>
              ) : (
                <span className={`flex items-center gap-1.5 text-sm ${status?.database.connected ? "text-emerald-600" : "text-red-500"}`}>
                  <StatusDot ok={status?.database.connected ?? false} />
                  {status?.database.version || (status?.database.connected ? "Connected" : "Disconnected")}
                </span>
              )}
            </div>

            {/* Redis */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Redis</span>
              {statusLoading ? (
                <span className="flex items-center gap-1.5 text-sm text-slate-400">
                  <StatusDot ok={false} loading /> Checking…
                </span>
              ) : (
                <span className={`flex items-center gap-1.5 text-sm ${status?.redis.connected ? "text-emerald-600" : "text-red-500"}`}>
                  <StatusDot ok={status?.redis.connected ?? false} />
                  {status?.redis.connected ? "Running" : "Not running"}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
