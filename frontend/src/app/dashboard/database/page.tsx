"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Database, Plus, Upload, Table2, X, Loader2, FileUp, Eye, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";

type Tab = "tables" | "create" | "upload-table" | "upload-data";

const ROWS_PAGE_SIZE = 50;

export default function DatabasePage() {
  const companyId = useCompanyId();
  const [tab, setTab] = useState<Tab>("tables");
  const [datasets, setDatasets] = useState<any[]>([]);
  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [loading, setLoading] = useState(false);

  // Create table form
  const [tableName, setTableName] = useState("");
  const [tableDesc, setTableDesc] = useState("");
  const [columns, setColumns] = useState([
    { name: "", type: "text", nullable: true },
  ]);

  // Upload table form
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState("");
  const [uploadDesc, setUploadDesc] = useState("");
  const [preview, setPreview] = useState<any>(null);
  const [sqlPreview, setSqlPreview] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const uploadTableInputRef = useRef<HTMLInputElement>(null);

  // Upload data form
  const [dataFile, setDataFile] = useState<File | null>(null);
  const [targetDataset, setTargetDataset] = useState<number | null>(null);
  const [importMode, setImportMode] = useState("append");
  const uploadDataInputRef = useRef<HTMLInputElement>(null);

  // Upload result
  const [uploadResult, setUploadResult] = useState<{ errors?: { table: string; step: string; error: string }[] } | null>(null);

  // View data
  const [viewingDataset, setViewingDataset] = useState<any | null>(null);
  const [viewData, setViewData] = useState<{ columns: string[]; rows: Record<string, unknown>[]; total: number } | null>(null);
  const [viewDataLoading, setViewDataLoading] = useState(false);
  const [viewPage, setViewPage] = useState(0);

  const loadDatasets = useCallback(async () => {
    if (!companyId) return;
    setDatasetsLoading(true);
    try {
      setDatasets(await api.getDatasets(companyId));
    } catch {
      setDatasets([]);
    } finally {
      setDatasetsLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    if (companyId) loadDatasets();
  }, [companyId, loadDatasets]);

  const handleCreateTable = async () => {
    if (!companyId || !tableName) return;
    setLoading(true);
    try {
      await api.createManualTable(companyId, {
        display_name: tableName,
        description: tableDesc || undefined,
        columns: columns.filter((c) => c.name),
      });
      await loadDatasets();
      setTab("tables");
      setTableName("");
      setTableDesc("");
      setColumns([{ name: "", type: "text", nullable: true }]);
    } catch {}
    setLoading(false);
  };

  const isSQL = uploadFile?.name.toLowerCase().endsWith(".sql");

  const handleUploadTable = async () => {
    if (!companyId || !uploadFile || !uploadName) return;
    setLoading(true);
    setUploadResult(null);
    try {
      if (isSQL) {
        const result = await api.uploadSQL(companyId, uploadFile, uploadName, uploadDesc);
        if (result?.errors?.length) {
          setUploadResult(result);
        } else {
          await loadDatasets();
          setTab("tables");
          setUploadFile(null);
          setUploadName("");
          setUploadDesc("");
          setPreview(null);
          setSqlPreview(null);
        }
        await loadDatasets();
      } else {
        await api.uploadTableAndData(companyId, uploadFile, uploadName, uploadDesc);
        await loadDatasets();
        setTab("tables");
        setUploadFile(null);
        setUploadName("");
        setUploadDesc("");
        setPreview(null);
        setSqlPreview(null);
      }
    } catch {}
    setLoading(false);
  };

  const handlePreview = async (file: File) => {
    if (!companyId) return;
    setUploadFile(file);
    setPreview(null);
    setSqlPreview(null);
    setPreviewLoading(true);
    try {
      if (file.name.toLowerCase().endsWith(".sql")) {
        setSqlPreview(await api.previewSQL(companyId, file));
      } else {
        setPreview(await api.previewCSV(companyId, file));
      }
    } catch {
      setPreview(null);
      setSqlPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleUploadData = async () => {
    if (!companyId || !dataFile || !targetDataset) return;
    setLoading(true);
    try {
      await api.uploadDataToTable(
        companyId,
        targetDataset,
        dataFile,
        importMode
      );
      await loadDatasets();
      setTab("tables");
      setDataFile(null);
      setTargetDataset(null);
    } catch {}
    setLoading(false);
  };

  const openViewData = useCallback(
    async (ds: any) => {
      if (!companyId) return;
      setViewingDataset(ds);
      setViewData(null);
      setViewPage(0);
      setViewDataLoading(true);
      try {
        const result = await api.getDatasetRows(companyId, ds.id, ROWS_PAGE_SIZE, 0);
        setViewData(result);
      } catch {
        setViewData(null);
      } finally {
        setViewDataLoading(false);
      }
    },
    [companyId]
  );

  const loadViewDataPage = useCallback(
    async (page: number) => {
      if (!companyId || !viewingDataset) return;
      setViewDataLoading(true);
      try {
        const result = await api.getDatasetRows(
          companyId,
          viewingDataset.id,
          ROWS_PAGE_SIZE,
          page * ROWS_PAGE_SIZE
        );
        setViewData(result);
        setViewPage(page);
      } catch {}
      setViewDataLoading(false);
    },
    [companyId, viewingDataset]
  );

  const addColumn = () =>
    setColumns([...columns, { name: "", type: "text", nullable: true }]);
  const removeColumn = (i: number) =>
    setColumns(columns.filter((_, idx) => idx !== i));
  const updateColumn = (i: number, field: string, value: unknown) => {
    const updated = [...columns];
    (updated[i] as Record<string, unknown>)[field] = value;
    setColumns(updated);
  };

  const tabs: { id: Tab; label: string; icon: typeof Table2 }[] = [
    { id: "tables", label: "Tables", icon: Table2 },
    { id: "create", label: "Create Table", icon: Plus },
    { id: "upload-table", label: "Upload Table & Data", icon: Upload },
    { id: "upload-data", label: "Upload Data", icon: Database },
  ];

  // Styled file input: visible button + hidden input
  const FileInputButton = ({
    refEl,
    accept,
    onSelect,
    label,
    selectedFile,
  }: {
    refEl: React.RefObject<HTMLInputElement | null>;
    accept: string;
    onSelect: (file: File) => void;
    label: string;
    selectedFile: File | null;
  }) => (
    <div className="space-y-1">
      <input
        ref={refEl}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onSelect(f);
        }}
      />
      <button
        type="button"
        onClick={() => refEl.current?.click()}
        className="flex items-center gap-2 px-4 py-2.5 rounded-lg border-2 border-slate-300 bg-white text-slate-700 text-sm font-medium hover:border-red-400 hover:bg-red-50 hover:text-red-700 transition-colors"
      >
        <FileUp size={18} />
        {selectedFile ? selectedFile.name : label}
      </button>
      {selectedFile && (
        <p className="text-xs text-slate-500">
          {(selectedFile.size / 1024).toFixed(1)} KB
        </p>
      )}
    </div>
  );

  if (!companyId)
    return (
      <div className="text-slate-400 text-center py-12">
        Select a company to manage databases
      </div>
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Database</h1>
        <p className="text-slate-500 mt-1">Manage tables and import data</p>
      </div>

      <div className="flex gap-1 bg-white rounded-lg border border-slate-200 p-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              tab === t.id ? "bg-red-600 text-white" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <t.icon size={16} />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tables tab */}
      {tab === "tables" && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          {datasetsLoading ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-500">
              <Loader2 size={32} className="animate-spin text-red-500 mb-3" />
              <p className="text-sm">Loading tables…</p>
            </div>
          ) : (
            <>
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Table</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Columns</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Rows</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Source</th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
                    <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {datasets.map((ds) => (
                    <tr key={ds.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm font-medium text-slate-900">{ds.display_name}</p>
                          <p className="text-xs text-slate-400">{ds.table_name}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600">{ds.columns_schema?.length || 0}</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{ds.row_count?.toLocaleString() ?? "—"}</td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 text-xs rounded-full bg-slate-100 text-slate-600">{ds.source}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            ds.status === "active" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {ds.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => openViewData(ds)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-600 bg-slate-100 hover:bg-red-100 hover:text-red-700 transition-colors"
                        >
                          <Eye size={14} /> View data
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!datasetsLoading && datasets.length === 0 && (
                <div className="text-center py-12 text-slate-400">No tables yet. Create one or upload a CSV / SQL file.</div>
              )}
            </>
          )}
        </div>
      )}

      {/* Create Table tab */}
      {tab === "create" && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Table Name</label>
              <input
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                placeholder="e.g. Sales Data"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
              <input
                value={tableDesc}
                onChange={(e) => setTableDesc(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                placeholder="Optional description"
              />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-700">Columns</label>
              <button onClick={addColumn} className="text-sm text-red-600 hover:text-red-700 font-medium">
                + Add Column
              </button>
            </div>
            <div className="space-y-2">
              {columns.map((col, i) => (
                <div key={i} className="flex gap-2 items-center">
                  <input
                    value={col.name}
                    onChange={(e) => updateColumn(i, "name", e.target.value)}
                    placeholder="Column name"
                    className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  />
                  <select
                    value={col.type}
                    onChange={(e) => updateColumn(i, "type", e.target.value)}
                    className="px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  >
                    <option value="text">Text</option>
                    <option value="integer">Integer</option>
                    <option value="float">Float</option>
                    <option value="boolean">Boolean</option>
                    <option value="date">Date</option>
                    <option value="timestamp">Timestamp</option>
                  </select>
                  <label className="flex items-center gap-1 text-sm text-slate-600">
                    <input type="checkbox" checked={col.nullable} onChange={(e) => updateColumn(i, "nullable", e.target.checked)} /> Null
                  </label>
                  {columns.length > 1 && (
                    <button onClick={() => removeColumn(i)} className="text-slate-400 hover:text-red-500">
                      <X size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
          <button
            onClick={handleCreateTable}
            disabled={loading || !tableName || columns.every((c) => !c.name)}
            className="px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="inline animate-spin mr-2" />
                Creating…
              </>
            ) : (
              "Create Table"
            )}
          </button>
        </div>
      )}

      {/* Upload Table & Data tab */}
      {tab === "upload-table" && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Display Name</label>
              <input
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                placeholder="e.g. Q1 Revenue"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
              <input
                value={uploadDesc}
                onChange={(e) => setUploadDesc(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">CSV or SQL File</label>
            <FileInputButton
              refEl={uploadTableInputRef}
              accept=".csv,.sql"
              onSelect={handlePreview}
              label="Choose CSV or SQL file"
              selectedFile={uploadFile}
            />
            {uploadFile && (
              <span className={`inline-block mt-1.5 px-2 py-0.5 text-xs font-medium rounded-full ${
                isSQL ? "bg-blue-100 text-blue-700" : "bg-emerald-100 text-emerald-700"
              }`}>
                {isSQL ? "SQL Dump" : "CSV"}
              </span>
            )}
          </div>

          {previewLoading && (
            <div className="flex items-center gap-2 text-slate-500 py-4">
              <Loader2 size={18} className="animate-spin text-red-500" />
              <span className="text-sm">Parsing file…</span>
            </div>
          )}

          {/* CSV Preview */}
          {preview && !sqlPreview && (
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">
                Preview ({preview.row_count} rows, {preview.columns?.length ?? 0} columns)
              </p>
              <div className="overflow-x-auto border border-slate-200 rounded-lg">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50">
                    <tr>
                      {(preview.columns || []).map((c: string) => (
                        <th key={c} className="px-3 py-2 text-left font-semibold text-slate-600">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(preview.preview_rows || []).slice(0, 5).map((row: Record<string, unknown>, i: number) => (
                      <tr key={i}>
                        {(preview.columns || []).map((c: string) => (
                          <td key={c} className="px-3 py-2 text-slate-700">
                            {String(row[c] ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SQL Preview */}
          {sqlPreview && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <p className="text-sm font-medium text-slate-700">
                  Found {sqlPreview.total_tables} table{sqlPreview.total_tables !== 1 ? "s" : ""} — {sqlPreview.total_rows.toLocaleString()} total rows
                </p>
              </div>
              {(sqlPreview.tables || []).map((t: any, idx: number) => (
                <div key={idx} className="border border-slate-200 rounded-lg overflow-hidden">
                  <div className="bg-slate-50 px-4 py-3 flex items-center justify-between">
                    <div>
                      <span className="text-sm font-semibold text-slate-900">{t.original_name}</span>
                      <span className="text-xs text-slate-400 ml-2">→ {t.target_name}</span>
                      <span className="text-xs text-slate-500 ml-3">{t.row_count.toLocaleString()} rows, {t.columns?.length ?? 0} cols</span>
                    </div>
                    {t.is_duplicate && (
                      <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 text-amber-700">
                        <AlertTriangle size={12} /> Renamed (original name existed)
                      </span>
                    )}
                  </div>
                  {/* Column list */}
                  <div className="px-4 py-2 text-xs text-slate-600 flex flex-wrap gap-2 border-b border-slate-100">
                    {(t.columns || []).map((col: any) => (
                      <span key={col.name} className="bg-slate-100 px-2 py-0.5 rounded">
                        {col.name} <span className="text-slate-400">{col.type}</span>
                      </span>
                    ))}
                  </div>
                  {/* Preview rows */}
                  {t.preview_rows?.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-slate-50">
                          <tr>
                            {(t.columns || []).map((col: any) => (
                              <th key={col.name} className="px-3 py-1.5 text-left font-semibold text-slate-600 whitespace-nowrap">
                                {col.name}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {t.preview_rows.slice(0, 5).map((row: any, ri: number) => (
                            <tr key={ri}>
                              {(t.columns || []).map((col: any) => (
                                <td key={col.name} className="px-3 py-1.5 text-slate-700 max-w-[200px] truncate" title={String(row[col.name] ?? "")}>
                                  {String(row[col.name] ?? "")}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {uploadResult?.errors?.length ? (
            <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 space-y-2">
              <p className="text-sm font-semibold text-amber-800 flex items-center gap-1.5">
                <AlertTriangle size={16} /> Some tables had import errors
              </p>
              {uploadResult.errors.map((e, i) => (
                <div key={i} className="text-xs text-amber-700">
                  <span className="font-medium">{e.table}</span> ({e.step}): {e.error}
                </div>
              ))}
            </div>
          ) : null}

          <button
            onClick={handleUploadTable}
            disabled={loading || !uploadFile || !uploadName}
            className="px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="inline animate-spin mr-2" />
                {isSQL ? "Importing SQL…" : "Creating…"}
              </>
            ) : (
              isSQL ? "Import SQL Tables" : "Create Table & Import"
            )}
          </button>
        </div>
      )}

      {/* Upload Data tab */}
      {tab === "upload-data" && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Target Table</label>
            <select
              value={targetDataset ?? ""}
              onChange={(e) => setTargetDataset(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            >
              <option value="">Select a table…</option>
              {datasets.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.display_name} ({ds.table_name})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">CSV File</label>
            <FileInputButton
              refEl={uploadDataInputRef}
              accept=".csv,.sql"
              onSelect={(f) => setDataFile(f)}
              label="Choose CSV file"
              selectedFile={dataFile}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Import Mode</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input type="radio" name="mode" value="append" checked={importMode === "append"} onChange={() => setImportMode("append")} />
                <span className="text-sm">Append</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="mode" value="replace" checked={importMode === "replace"} onChange={() => setImportMode("replace")} />
                <span className="text-sm">Replace</span>
              </label>
            </div>
          </div>
          <button
            onClick={handleUploadData}
            disabled={loading || !dataFile || !targetDataset}
            className="px-4 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="inline animate-spin mr-2" />
                Importing…
              </>
            ) : (
              "Import Data"
            )}
          </button>
        </div>
      )}

      {/* View Data modal */}
      {viewingDataset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => setViewingDataset(null)}>
          <div
            className="bg-white rounded-xl shadow-xl max-w-[90vw] max-h-[85vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">
                {viewingDataset.display_name} <span className="text-slate-400 font-normal">({viewingDataset.table_name})</span>
              </h2>
              <button
                onClick={() => setViewingDataset(null)}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              {viewDataLoading ? (
                <div className="flex flex-col items-center justify-center py-16 text-slate-500">
                  <Loader2 size={32} className="animate-spin text-red-500 mb-3" />
                  <p className="text-sm">Loading rows…</p>
                </div>
              ) : viewData ? (
                <>
                  <p className="text-sm text-slate-500 mb-3">
                    Showing {viewData.rows.length} of {viewData.total.toLocaleString()} rows
                  </p>
                  <div className="overflow-x-auto border border-slate-200 rounded-lg">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left font-semibold text-slate-600 border-b border-slate-200">#</th>
                          {viewData.columns.map((c) => (
                            <th key={c} className="px-4 py-2 text-left font-semibold text-slate-600 border-b border-slate-200 whitespace-nowrap">
                              {c}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {viewData.rows.map((row, i) => (
                          <tr key={(row.id as number) ?? i} className="hover:bg-slate-50">
                            <td className="px-4 py-2 text-slate-500 border-b border-slate-100">
                              {viewPage * ROWS_PAGE_SIZE + i + 1}
                            </td>
                            {viewData.columns.map((col) => (
                              <td key={col} className="px-4 py-2 text-slate-700 border-b border-slate-100 max-w-[200px] truncate" title={String(row[col] ?? "")}>
                                {String(row[col] ?? "")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {viewData.total > ROWS_PAGE_SIZE && (
                    <div className="flex items-center justify-between mt-4">
                      <button
                        onClick={() => loadViewDataPage(viewPage - 1)}
                        disabled={viewPage === 0}
                        className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-slate-500">
                        Page {viewPage + 1} of {Math.ceil(viewData.total / ROWS_PAGE_SIZE)}
                      </span>
                      <button
                        onClick={() => loadViewDataPage(viewPage + 1)}
                        disabled={(viewPage + 1) * ROWS_PAGE_SIZE >= viewData.total}
                        className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-slate-500 py-8">No data or failed to load.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
