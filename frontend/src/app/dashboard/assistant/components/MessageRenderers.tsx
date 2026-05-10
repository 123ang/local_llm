import { BarChart3, Copy, Database, FileText, HelpCircle, Lightbulb, ShieldCheck } from "lucide-react";

export function MessageContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const blocks: Array<{ type: "text"; lines: string[] } | { type: "table"; lines: string[] }> = [];
  let i = 0;

  const isTableSeparator = (line: string) => /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
  const isTableRow = (line: string) => line.trim().startsWith("|") && line.trim().endsWith("|");

  while (i < lines.length) {
    if (isTableRow(lines[i]) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const tableLines = [lines[i], lines[i + 1]];
      i += 2;
      while (i < lines.length && isTableRow(lines[i])) {
        tableLines.push(lines[i]);
        i += 1;
      }
      blocks.push({ type: "table", lines: tableLines });
    } else {
      const textLines: string[] = [];
      while (i < lines.length && !(isTableRow(lines[i]) && i + 1 < lines.length && isTableSeparator(lines[i + 1]))) {
        textLines.push(lines[i]);
        i += 1;
      }
      blocks.push({ type: "text", lines: textLines });
    }
  }

  const splitCells = (line: string) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(cell => cell.trim());
  const renderInline = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={idx}>{part.slice(2, -2)}</strong>;
      }
      return <span key={idx}>{part}</span>;
    });
  };

  return (
    <div className="text-sm space-y-2">
      {blocks.map((block, idx) => {
        if (block.type === "text") {
          const text = block.lines.join("\n").trim();
          if (!text) return null;
          return <p key={idx} className="whitespace-pre-wrap">{renderInline(text)}</p>;
        }

        const headers = splitCells(block.lines[0]);
        const rows = block.lines.slice(2).map(splitCells);
        return (
          <div key={idx} className="my-3 overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-xs">
              <thead className="bg-slate-100">
                <tr>
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="px-3 py-2 text-left font-semibold text-slate-700 whitespace-nowrap border-b border-slate-200">
                      {renderInline(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-slate-50">
                    {headers.map((_, cIdx) => (
                      <td key={cIdx} className="px-3 py-2 text-slate-700 whitespace-nowrap">
                        {renderInline(row[cIdx] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}

export function DatabaseResultTable({ data }: { data: any }) {
  if (!data) return null;
  const result = data.result;
  if (!result || typeof result === "string") return null;
  if (!Array.isArray(result) || result.length === 0) return null;

  const cols = Object.keys(result[0]);
  return (
    <details className="mt-3 group rounded-lg border border-slate-200 bg-white">
      <summary className="cursor-pointer select-none list-none px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 rounded-lg flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5">
          <Database size={12} className="text-emerald-600" />
          Show database rows ({result.length})
        </span>
        <span className="text-slate-400 group-open:rotate-180 transition-transform">⌄</span>
      </summary>
      <div className="overflow-x-auto border-t border-slate-200">
        <table className="w-full text-xs">
          <thead className="bg-slate-100">
            <tr>
              {cols.map(c => (
                <th key={c} className="px-3 py-1.5 text-left font-semibold text-slate-600 whitespace-nowrap">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {result.slice(0, 20).map((row: Record<string, unknown>, i: number) => (
              <tr key={i} className="hover:bg-slate-50">
                {cols.map(c => (
                  <td key={c} className="px-3 py-1.5 text-slate-700 whitespace-nowrap max-w-[180px] truncate" title={String(row[c] ?? "")}>
                    {String(row[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {result.length > 20 && (
          <p className="px-3 py-1.5 text-xs text-slate-400 bg-slate-50 border-t border-slate-200">
            Showing 20 of {result.length} rows
          </p>
        )}
      </div>
    </details>
  );
}

async function openPdfSource(doc: any) {
  if (!doc.company_id || !doc.document_id) return;
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const res = await fetch(`/api/documents/${doc.company_id}/${doc.document_id}/file`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) return;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(`${url}${doc.page ? `#page=${doc.page}` : ""}`, "_blank", "noopener,noreferrer");
}

export function SourceBadges({ sources }: { sources: any }) {
  if (!sources) return null;
  const docs = sources.documents || [];
  const faq = sources.faq || [];
  const db = sources.database;
  const hasFaq = faq.length > 0;
  const hasDocs = docs.length > 0;
  const hasDb = !!db;
  if (!hasFaq && !hasDocs && !hasDb) return null;

  return (
    <div className="mt-3 space-y-2">
      <div className="flex flex-wrap gap-2">
        {hasFaq && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-amber-50 text-amber-700 text-xs font-medium border border-amber-200">
            <HelpCircle size={11} /> {faq.length} FAQ
          </span>
        )}
        {hasDocs && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-medium border border-blue-200">
            <FileText size={11} /> {docs.length} PDF passage{docs.length === 1 ? "" : "s"}
          </span>
        )}
        {hasDb && (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-200">
            <Database size={11} /> {db.row_count ?? 0} database row{db.row_count === 1 ? "" : "s"}
          </span>
        )}
      </div>

      <details className="group rounded-lg border border-slate-200 bg-white">
        <summary className="cursor-pointer select-none list-none px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 rounded-lg flex items-center justify-between">
          <span className="inline-flex items-center gap-1.5">
            <ShieldCheck size={12} className="text-slate-500" /> Answer audit trail
          </span>
          <span className="text-slate-400 group-open:rotate-180 transition-transform">⌄</span>
        </summary>
        <div className="border-t border-slate-200 p-3 space-y-3 text-xs text-slate-600">
          {hasDocs && (
            <div>
              <div className="font-semibold text-slate-700 mb-1">Documents</div>
              <div className="space-y-2">
                {docs.map((doc: any, i: number) => (
                  <div key={i} className="rounded-md bg-blue-50 border border-blue-100 p-2">
                    <button type="button" onClick={() => openPdfSource(doc)} className="font-medium text-blue-700 hover:underline text-left">
                      Source: {doc.source}{doc.page ? `, page ${doc.page}` : ""}
                    </button>
                    {doc.score !== undefined && <div className="text-blue-600/70 mt-0.5">Relevance: {doc.score}</div>}
                    {doc.content && <div className="mt-1 text-slate-600 line-clamp-3">“{doc.content}”</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
          {hasDb && (
            <div>
              <div className="font-semibold text-slate-700 mb-1">Database</div>
              <div className="rounded-md bg-emerald-50 border border-emerald-100 p-2">
                <div>Source: {(db.datasets || db.tables || ["Database"]).join(", ")}</div>
                <div>Rows returned: {db.row_count ?? 0}</div>
                {db.sql && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-emerald-700 font-medium">Show SQL</summary>
                    <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded bg-white p-2 text-[11px] text-slate-600 border border-emerald-100">{db.sql}</pre>
                  </details>
                )}
              </div>
            </div>
          )}
          {hasFaq && (
            <div>
              <div className="font-semibold text-slate-700 mb-1">FAQ</div>
              <div className="space-y-2">
                {faq.map((item: any, i: number) => (
                  <div key={i} className="rounded-md bg-amber-50 border border-amber-100 p-2">
                    <div className="font-medium text-amber-700">{item.question}</div>
                    <div className="mt-1 text-slate-600 line-clamp-2">{item.answer}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </details>
    </div>
  );
}

function extractKeyAnswer(content: string): string {
  const lines = content.split("\n").map(line => line.trim()).filter(Boolean);
  const firstText = lines.find(line => !line.startsWith("|") && !/^:?-{3,}/.test(line));
  return firstText?.replace(/^#+\s*/, "") || "Answer generated from selected sources";
}

function sourceSummary(sources: any) {
  const docs = sources?.documents?.length || 0;
  const faq = sources?.faq?.length || 0;
  const dbRows = sources?.database?.row_count ?? 0;
  const parts = [];
  if (dbRows) parts.push(`${dbRows} database row${dbRows === 1 ? "" : "s"}`);
  if (docs) parts.push(`${docs} PDF passage${docs === 1 ? "" : "s"}`);
  if (faq) parts.push(`${faq} FAQ`);
  return parts.length ? parts.join(" · ") : "No source evidence attached";
}

function NumericResultChart({ data }: { data: any }) {
  const rows = Array.isArray(data?.result) ? data.result : [];
  if (!rows.length) return null;

  const cols = Object.keys(rows[0] || {});
  const numericCols = cols.filter(col => rows.some((row: any) => Number.isFinite(Number(row[col]))));
  const labelCol = cols.find(col => !numericCols.includes(col) && rows.some((row: any) => row[col])) || cols[0];
  const valueCol = numericCols.find(col => /score|rate|ratio|jobs|count|total|amount|value|percentage|percent/i.test(col)) || numericCols[0];
  if (!labelCol || !valueCol) return null;

  const chartRows = rows
    .map((row: any) => ({ label: String(row[labelCol] ?? "—"), value: Number(row[valueCol]) }))
    .filter((row: any) => Number.isFinite(row.value))
    .slice(0, 8);
  if (chartRows.length < 2) return null;

  const max = Math.max(...chartRows.map((row: any) => Math.abs(row.value)), 1);
  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3">
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-slate-700">
        <BarChart3 size={14} className="text-red-500" /> Quick chart: {valueCol}
      </div>
      <div className="space-y-2">
        {chartRows.map((row: any, idx: number) => (
          <div key={`${row.label}-${idx}`} className="grid grid-cols-[minmax(90px,180px)_1fr_auto] items-center gap-2 text-xs">
            <div className="truncate text-slate-600" title={row.label}>{row.label}</div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-red-500" style={{ width: `${Math.max(4, Math.round(Math.abs(row.value) / max * 100))}%` }} />
            </div>
            <div className="tabular-nums text-slate-700">{row.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RecommendationBlock({ content, hasSources }: { content: string; hasSources: boolean }) {
  const insightLines = content
    .split("\n")
    .map(line => line.trim())
    .filter(line => /^(insight|recommendation|recommended action|next step|why this matters)\s*:/i.test(line));
  if (!insightLines.length) return null;
  return (
    <div className="mt-3 rounded-xl border border-purple-200 bg-purple-50 p-3 text-xs text-purple-800">
      <div className="mb-1 flex items-center gap-1.5 font-semibold">
        <Lightbulb size={13} /> {hasSources ? "Insight / recommended action" : "AI insight"}
      </div>
      <div className="space-y-1">
        {insightLines.map((line, idx) => <p key={idx}>{line}</p>)}
      </div>
    </div>
  );
}

export function ExecutiveAnswerCard({ content, sources }: { content: string; sources: any }) {
  const hasSources = Boolean(sources?.database || sources?.documents?.length || sources?.faq?.length);
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white p-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Executive answer</div>
            <div className="mt-1 text-sm font-semibold text-slate-900">{extractKeyAnswer(content)}</div>
          </div>
          <button
            type="button"
            onClick={() => navigator.clipboard?.writeText(content)}
            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-500 hover:bg-slate-50"
            title="Copy answer"
          >
            <Copy size={12} /> Copy
          </button>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
          <span className={`rounded-full px-2 py-0.5 ${hasSources ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-slate-100 text-slate-500"}`}>
            {hasSources ? "Evidence-backed" : "No evidence attached"}
          </span>
          <span>{sourceSummary(sources)}</span>
        </div>
      </div>
      <div className="p-3">
        <MessageContent content={content} />
        <NumericResultChart data={sources?.database} />
        <RecommendationBlock content={content} hasSources={hasSources} />
      </div>
    </div>
  );
}
