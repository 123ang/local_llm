"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Upload, Trash2, FileText, Loader2, RefreshCw, AlertCircle, CheckCircle, Clock } from "lucide-react";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";

export default function DocumentsPage() {
  const companyId = useCompanyId();
  const [docs, setDocs] = useState<any[]>([]);
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

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !companyId) return;
    setUploading(true);
    try {
      await api.uploadDocument(companyId, file);
      await loadDocs();
    } catch (err: any) {
      alert(err.message || "Upload failed");
    }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleReprocess = async (docId: number) => {
    if (!companyId) return;
    setReprocessing(docId);
    try {
      await api.request(`/documents/${companyId}/${docId}/reprocess`, { method: "POST" });
      await loadDocs();
    } catch (err: any) {
      alert(err.message || "Reprocess failed");
    }
    setReprocessing(null);
  };

  const handleDelete = async (docId: number) => {
    if (!companyId || !confirm("Delete this document and all its chunks?")) return;
    try {
      await api.deleteDocument(companyId, docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch {}
  };

  const StatusBadge = ({ status, errorMessage }: { status: string; errorMessage?: string }) => {
    const configs: Record<string, { cls: string; icon: React.ReactNode; label: string }> = {
      pending:    { cls: "bg-amber-50 text-amber-700 border border-amber-200",   icon: <Clock size={11} />,        label: "Pending" },
      processing: { cls: "bg-blue-50 text-blue-700 border border-blue-200",      icon: <Loader2 size={11} className="animate-spin" />, label: "Processing" },
      ready:      { cls: "bg-emerald-50 text-emerald-700 border border-emerald-200", icon: <CheckCircle size={11} />, label: "Ready" },
      error:      { cls: "bg-red-50 text-red-700 border border-red-200",          icon: <AlertCircle size={11} />,  label: "Error" },
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
      <div className="text-slate-400 text-center py-12">Select a company to manage documents</div>
    );

  const processingCount = docs.filter((d) => d.status === "pending" || d.status === "processing").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Documents</h1>
          <p className="text-slate-500 mt-1">
            Upload PDFs — they are automatically parsed, chunked, and embedded for semantic search.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {processingCount > 0 && (
            <span className="flex items-center gap-1.5 text-sm text-blue-600 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg">
              <Loader2 size={13} className="animate-spin" />
              {processingCount} processing…
            </span>
          )}
          <label className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium cursor-pointer transition-colors">
            {uploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            {uploading ? "Uploading…" : "Upload PDF"}
            <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} disabled={uploading} />
          </label>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Document</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Pages</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Chunks</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Size</th>
              <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Uploaded</th>
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
                <td className="px-6 py-4 text-sm text-slate-600">{doc.page_count || "—"}</td>
                <td className="px-6 py-4 text-sm text-slate-600">{doc.chunk_count || 0}</td>
                <td className="px-6 py-4 text-sm text-slate-600">
                  {doc.file_size ? `${(doc.file_size / 1024).toFixed(0)} KB` : "—"}
                </td>
                <td className="px-6 py-4 text-sm text-slate-500">
                  {new Date(doc.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-1">
                    {(doc.status === "error" || doc.status === "pending") && (
                      <button
                        onClick={() => handleReprocess(doc.id)}
                        disabled={reprocessing === doc.id}
                        className="p-1.5 text-slate-400 hover:text-blue-500 rounded-lg hover:bg-blue-50 transition-colors"
                        title="Retry processing"
                      >
                        {reprocessing === doc.id
                          ? <Loader2 size={15} className="animate-spin" />
                          : <RefreshCw size={15} />}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                      title="Delete document"
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
            No documents uploaded yet. Upload a PDF to get started.
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
        <strong>How PDF processing works:</strong> After uploading, the file is automatically parsed into pages,
        split into overlapping chunks (~800 chars), and each chunk is embedded using{" "}
        <code className="bg-blue-100 px-1 rounded">nomic-embed-text</code> via Ollama.
        When you ask a question in the Assistant, the most semantically similar chunks are retrieved and fed to the LLM.
        Processing time depends on the PDF size — a 10-page document takes ~30 seconds.
      </div>
    </div>
  );
}
