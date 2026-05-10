import { Database, FileText, HelpCircle } from "lucide-react";

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

export function SourceBadges({ sources }: { sources: any }) {
  if (!sources) return null;
  const hasFaq = sources.faq?.length > 0;
  const hasDocs = sources.documents?.length > 0;
  const hasDb = sources.database;
  if (!hasFaq && !hasDocs && !hasDb) return null;

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {hasFaq && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-amber-50 text-amber-700 text-xs font-medium border border-amber-200">
          <HelpCircle size={11} /> {sources.faq.length} FAQ
        </span>
      )}
      {hasDocs && sources.documents.map((doc: any, i: number) => (
        <span key={i} className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-blue-50 text-blue-700 text-xs font-medium border border-blue-200">
          <FileText size={11} /> {doc.source}{doc.page ? `, p.${doc.page}` : ""}
        </span>
      ))}
      {hasDb && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-200">
          <Database size={11} /> {hasDb.row_count ?? 0} rows from database
        </span>
      )}
    </div>
  );
}
