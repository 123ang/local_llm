"use client";
import { useEffect, useState } from "react";
import { Download, FileJson, Play, Plus, Trash2, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";

const SOURCE_OPTIONS = ["database", "documents", "faq"];

function csvCell(value: unknown): string {
  const text = Array.isArray(value) || (value && typeof value === "object") ? JSON.stringify(value) : String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}

function downloadTextFile(filename: string, mimeType: string, content: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function EvaluationsPage() {
  const companyId = useCompanyId();
  const [questions, setQuestions] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [form, setForm] = useState({ question: "", expected_keywords: "", expected_source: "", sources: SOURCE_OPTIONS, ai_insights: false });

  const load = async () => {
    if (!companyId) return;
    setLoading(true);
    try {
      const [q, r] = await Promise.all([api.getEvaluationQuestions(companyId), api.getEvaluationRuns(companyId)]);
      setQuestions(q);
      setRuns(r);
    } catch {
      setQuestions([]);
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [companyId]);

  const createQuestion = async () => {
    if (!companyId || !form.question.trim()) return;
    await api.createEvaluationQuestion(companyId, {
      question: form.question.trim(),
      expected_keywords: form.expected_keywords.split(",").map(s => s.trim()).filter(Boolean),
      expected_source: form.expected_source.trim() || null,
      sources: form.sources,
      ai_insights: form.ai_insights,
    });
    setForm({ question: "", expected_keywords: "", expected_source: "", sources: SOURCE_OPTIONS, ai_insights: false });
    await load();
  };

  const runQuestion = async (id: number) => {
    if (!companyId) return;
    setRunningId(id);
    try {
      await api.runEvaluationQuestion(companyId, id);
      await load();
    } finally {
      setRunningId(null);
    }
  };

  const deleteQuestion = async (id: number) => {
    if (!companyId) return;
    await api.deleteEvaluationQuestion(companyId, id);
    await load();
  };

  const toggleSource = (source: string) => {
    setForm(prev => {
      const set = new Set(prev.sources);
      if (set.has(source)) {
        if (set.size > 1) set.delete(source);
      } else set.add(source);
      return { ...prev, sources: Array.from(set) };
    });
  };

  const latestRun = (questionId: number) => runs.find(r => r.question_id === questionId);
  const passCount = runs.filter(r => r.passed).length;
  const exportRows = () => runs.map(run => {
    const question = questions.find(q => q.id === run.question_id);
    return {
      run_id: run.id,
      question_id: run.question_id,
      question: question?.question ?? "",
      passed: run.passed,
      latency_ms: run.latency_ms ?? "",
      model_tier: run.model_tier ?? "",
      missing_keywords: run.missing_keywords || [],
      expected_keywords: question?.expected_keywords || [],
      expected_source: question?.expected_source ?? "",
      answer: run.answer,
      sources_used: run.sources_used,
      created_at: run.created_at,
    };
  });
  const exportCsv = () => {
    const rows = exportRows();
    const headers = ["run_id", "question_id", "question", "passed", "latency_ms", "model_tier", "missing_keywords", "expected_keywords", "expected_source", "answer", "sources_used", "created_at"];
    const csv = [headers.join(","), ...rows.map(row => headers.map(header => csvCell(row[header as keyof typeof row])).join(","))].join("\n");
    downloadTextFile("andai-evaluation-results.csv", "text/csv;charset=utf-8", csv);
  };
  const exportJson = () => {
    downloadTextFile("andai-evaluation-results.json", "application/json;charset=utf-8", JSON.stringify(exportRows(), null, 2));
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Evaluation Tests</h1>
            <p className="text-slate-500 mt-1">Save regression questions and verify answers, sources, latency, and model tier.</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button onClick={exportCsv} disabled={!runs.length} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50">
              <Download size={15} /> CSV
            </button>
            <button onClick={exportJson} disabled={!runs.length} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-50">
              <FileJson size={15} /> JSON
            </button>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4"><p className="text-xs text-slate-400">Questions</p><p className="text-2xl font-bold">{questions.length}</p></div>
        <div className="bg-white rounded-xl border border-slate-200 p-4"><p className="text-xs text-slate-400">Runs</p><p className="text-2xl font-bold">{runs.length}</p></div>
        <div className="bg-white rounded-xl border border-slate-200 p-4"><p className="text-xs text-slate-400">Pass rate</p><p className="text-2xl font-bold">{runs.length ? Math.round(passCount / runs.length * 100) : 0}%</p></div>
        <div className="bg-white rounded-xl border border-slate-200 p-4"><p className="text-xs text-slate-400">Avg latency</p><p className="text-2xl font-bold">{runs.length ? (runs.reduce((s,r)=>s+(r.latency_ms||0),0)/runs.length/1000).toFixed(1) : "0.0"}s</p></div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
        <h2 className="font-semibold text-slate-900">Add test question</h2>
        <input value={form.question} onChange={e => setForm({ ...form, question: e.target.value })} placeholder="Question" className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm" />
        <div className="grid md:grid-cols-2 gap-3">
          <input value={form.expected_keywords} onChange={e => setForm({ ...form, expected_keywords: e.target.value })} placeholder="Expected keywords, comma separated" className="px-3 py-2 rounded-lg border border-slate-300 text-sm" />
          <input value={form.expected_source} onChange={e => setForm({ ...form, expected_source: e.target.value })} placeholder="Expected source name/table/PDF" className="px-3 py-2 rounded-lg border border-slate-300 text-sm" />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500">Sources:</span>
          {SOURCE_OPTIONS.map(s => <button key={s} onClick={() => toggleSource(s)} className={`px-2.5 py-1.5 text-xs rounded-lg border ${form.sources.includes(s) ? "bg-red-50 text-red-700 border-red-300" : "bg-white text-slate-400 border-slate-200"}`}>{s}</button>)}
          <label className="ml-2 inline-flex items-center gap-1.5 text-xs text-slate-600"><input type="checkbox" checked={form.ai_insights} onChange={e => setForm({ ...form, ai_insights: e.target.checked })} /> AI Insights</label>
          <button onClick={createQuestion} className="ml-auto inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-red-600 text-white text-sm"><Plus size={14}/> Add</button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200"><tr><th className="px-4 py-3 text-left">Question</th><th className="px-4 py-3 text-left">Expected</th><th className="px-4 py-3 text-left">Latest result</th><th className="px-4 py-3"></th></tr></thead>
          <tbody className="divide-y divide-slate-100">
            {questions.map(q => { const r = latestRun(q.id); return (
              <tr key={q.id} className="align-top">
                <td className="px-4 py-3 max-w-md"><div className="font-medium text-slate-800">{q.question}</div><div className="mt-1 text-xs text-slate-400">{q.sources.join(", ")} · {q.ai_insights ? "AI Insights" : "Source Only"}</div></td>
                <td className="px-4 py-3 text-xs text-slate-500">Keywords: {(q.expected_keywords||[]).join(", ") || "—"}<br/>Source: {q.expected_source || "—"}</td>
                <td className="px-4 py-3">{r ? <div className="space-y-1">{r.passed ? <span className="inline-flex items-center gap-1 text-emerald-700"><CheckCircle2 size={14}/> Pass</span> : <span className="inline-flex items-center gap-1 text-red-700"><XCircle size={14}/> Fail</span>}<div className="text-xs text-slate-400">{(r.latency_ms/1000).toFixed(1)}s · {r.model_tier || "—"}</div>{r.missing_keywords?.length > 0 && <div className="text-xs text-red-500">Missing: {r.missing_keywords.join(", ")}</div>}</div> : <span className="text-slate-400">Not run</span>}</td>
                <td className="px-4 py-3 text-right"><button onClick={() => runQuestion(q.id)} disabled={runningId===q.id} className="inline-flex items-center gap-1 px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs mr-2">{runningId===q.id ? <Loader2 size={13} className="animate-spin"/> : <Play size={13}/>} Run</button><button onClick={() => deleteQuestion(q.id)} className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-50 text-red-700 border border-red-200 text-xs"><Trash2 size={13}/></button></td>
              </tr>
            );})}
          </tbody>
        </table>
        {!loading && questions.length === 0 && <div className="py-10 text-center text-slate-400">No test questions yet</div>}
      </div>
    </div>
  );
}
