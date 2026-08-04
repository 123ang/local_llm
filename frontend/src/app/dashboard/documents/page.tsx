"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Upload, Trash2, FileText, Loader2, RefreshCw, AlertCircle, CheckCircle, Clock } from "lucide-react";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";
import { useI18n } from "@/lib/i18n-context";

export default function DocumentsPage() {
  const { t, formatDate } = useI18n();
  const companyId = useCompanyId();
  const [docs, setDocs] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [departmentId, setDepartmentId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const [reprocessing, setReprocessing] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadDocs = useCallback(async () => {
    if (!companyId) return;
    try {
      const data = await api.getDocuments(companyId);
      setDocs(data);
      // Auto-poll if any doc is still processing
      const hasProcessing = data.some((d: any) => d.status === "pending" || d.status === "processing");
      if (hasProcessing) {
        pollRef.current = setTimeout(loadDocs, 3000);
      }
    } catch {}
  }, [companyId]);

  useEffect(() => {
    if (companyId) loadDocs();
    return () => { if (pollRef.current) clearTimeout(pollRef.current); };
  }, [companyId, loadDocs]);

  useEffect(() => {
    if (!companyId) return;
    api.getDepartments(companyId).then((items) => {
      setDepartments(items);
      setDepartmentId((current) => current ?? items[0]?.id ?? null);
    }).catch(() => {
      setDepartments([]);
      setDepartmentId(null);
    });
  }, [companyId]);

  useEffect(() => {
    if (!uploading) return;

    const previousOverflow = document.body.style.overflow;
    const warnBeforeLeaving = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("beforeunload", warnBeforeLeaving);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("beforeunload", warnBeforeLeaving);
    };
  }, [uploading]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !companyId || !departmentId) return;
    setUploading(true);
    try {
      await api.uploadDocument(companyId, file, departmentId);
      await loadDocs();
    } catch (err: any) {
      alert(err.message || t("documents.uploadFailed"));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleReprocess = async (docId: number) => {
    if (!companyId) return;
    setReprocessing(docId);
    try {
      await api.request(`/documents/${companyId}/${docId}/reprocess`, { method: "POST" });
      await loadDocs();
    } catch (err: any) {
      alert(err.message || t("documents.reprocessFailed"));
    }
    setReprocessing(null);
  };

  const handleDelete = async (docId: number) => {
    if (!companyId || !confirm(t("documents.confirmDelete"))) return;
    try {
      await api.deleteDocument(companyId, docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch {}
  };

  const StatusBadge = ({ status, errorMessage }: { status: string; errorMessage?: string }) => {
    const configs: Record<string, { cls: string; icon: React.ReactNode; label: string }> = {
      pending:    { cls: "bg-amber-50 text-amber-700 border border-amber-200",   icon: <Clock size={11} />,        label: t("documents.pending") },
      processing: { cls: "bg-blue-50 text-blue-700 border border-blue-200",      icon: <Loader2 size={11} className="animate-spin" />, label: t("documents.processing") },
      ready:      { cls: "bg-emerald-50 text-emerald-700 border border-emerald-200", icon: <CheckCircle size={11} />, label: t("documents.ready") },
      error:      { cls: "bg-red-50 text-red-700 border border-red-200",          icon: <AlertCircle size={11} />,  label: t("documents.error") },
    };
    const cfg = configs[status] || { cls: "bg-slate-100 text-slate-600 border border-slate-200", icon: null, label: status };
    return (
      <div className="flex flex-col gap-1">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full w-fit ${cfg.cls}`}>
          {cfg.icon} {cfg.label}
        </span>
        {status === "error" && errorMessage && (
          <span className="text-xs text-red-500 max-w-[200px] truncate" title={errorMessage}>{errorMessage}</span>
        )}
      </div>
    );
  };

  if (!companyId)
    return (
      <div className="text-slate-400 text-center py-12">{t("documents.selectOrganization")}</div>
    );

  if (departments.length === 0)
    return (
      <div className="text-slate-400 text-center py-12">{t("documents.noDepartment")}</div>
    );

  const processingCount = docs.filter((d) => d.status === "pending" || d.status === "processing").length;

  return (
    <div className="space-y-6">
      {uploading && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-[1px] cursor-wait"
          role="status"
          aria-live="assertive"
          aria-busy="true"
        >
          <div className="w-[min(90vw,360px)] rounded-lg border border-slate-200 bg-white px-6 py-7 text-center shadow-2xl">
            <Loader2 size={32} className="mx-auto animate-spin text-red-600" aria-hidden="true" />
            <h2 className="mt-4 text-base font-semibold text-slate-900">{t("documents.uploadingTitle")}</h2>
            <p className="mt-2 text-sm leading-5 text-slate-600">
              {t("documents.uploadingCopy")}
            </p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("documents.title")}</h1>
          <p className="text-slate-500 mt-1">
            {t("documents.copy")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={departmentId ?? ""}
            onChange={(e) => setDepartmentId(e.target.value ? Number(e.target.value) : null)}
            className="px-3 py-2.5 border border-slate-300 rounded-lg text-sm bg-white"
          >
            {departments.map((department) => (
              <option key={department.id} value={department.id}>{department.name}</option>
            ))}
          </select>
          {processingCount > 0 && (
            <span className="flex items-center gap-1.5 text-sm text-blue-600 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg">
              <Loader2 size={13} className="animate-spin" />
              {t("documents.processingCount", { count: processingCount })}
            </span>
          )}
          <label className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium cursor-pointer transition-colors">
            {uploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            {uploading ? t("documents.uploading") : t("documents.upload")}
            <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={handleUpload} disabled={uploading || !departmentId} />
          </label>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("documents.document")}</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("documents.status")}</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("documents.department")}</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("documents.pages")}</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("documents.chunks")}</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("documents.size")}</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">{t("documents.uploaded")}</th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {docs.map((doc) => (
              <tr key={doc.id} className="hover:bg-slate-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <FileText size={18} className="text-red-500 shrink-0" />
                    <span className="text-sm font-medium text-slate-900 truncate max-w-[220px]" title={doc.original_name}>
                      {doc.original_name}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <StatusBadge status={doc.status} errorMessage={doc.error_message} />
                </td>
                <td className="px-6 py-4 text-sm text-slate-600">
                  {departments.find((department) => department.id === doc.department_id)?.name || "—"}
                </td>
                <td className="px-6 py-4 text-sm text-slate-600">{doc.page_count || "—"}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{doc.chunk_count || 0}</td>
                <td className="px-6 py-4 text-sm text-slate-600">
                  {doc.file_size ? `${(doc.file_size / 1024).toFixed(0)} KB` : "—"}
                </td>
                <td className="px-6 py-4 text-sm text-slate-500">
                  {formatDate(doc.created_at)}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-1">
                    {(doc.status === "error" || doc.status === "pending") && (
                      <button
                        onClick={() => handleReprocess(doc.id)}
                        disabled={reprocessing === doc.id}
                        className="p-1.5 text-slate-400 hover:text-blue-500 rounded-lg hover:bg-blue-50 transition-colors"
                        title={t("documents.retryProcessing")}
                      >
                        {reprocessing === doc.id
                          ? <Loader2 size={15} className="animate-spin" />
                          : <RefreshCw size={15} />}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                      title={t("documents.deleteDocument")}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {docs.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            {t("documents.empty")}
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <strong>{t("documents.howTitle")}</strong> {t("documents.howCopy")}
      </div>
    </div>
  );
}
