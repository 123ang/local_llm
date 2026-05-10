import { BarChart3, BriefcaseBusiness, Copy, Database, Download, FileText, HelpCircle, Lightbulb, ShieldCheck } from "lucide-react";

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

function groupDocumentCitations(docs: any[]): any[] {
  const grouped = new Map<string, any>();
  for (const doc of docs) {
    const key = `${doc.document_id ?? doc.source}|${doc.page ?? "unknown"}`;
    const existing = grouped.get(key);
    if (!existing) {
      grouped.set(key, { ...doc, passages: [doc.content].filter(Boolean), passage_count: 1 });
      continue;
    }
    existing.passage_count += 1;
    if (doc.content && !existing.passages.includes(doc.content)) existing.passages.push(doc.content);
    if (doc.score !== undefined && (existing.score === undefined || Number(doc.score) > Number(existing.score))) {
      existing.score = doc.score;
    }
  }
  return Array.from(grouped.values());
}

export function SourceBadges({ sources }: { sources: any }) {
  if (!sources) return null;
  const docs = sources.documents || [];
  const groupedDocs = groupDocumentCitations(docs);
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
            <FileText size={11} /> {docs.length} PDF passage{docs.length === 1 ? "" : "s"} on {groupedDocs.length} page{groupedDocs.length === 1 ? "" : "s"}
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
                {groupedDocs.map((doc: any, i: number) => (
                  <div key={i} className="rounded-md bg-blue-50 border border-blue-100 p-2">
                    <button type="button" onClick={() => openPdfSource(doc)} className="font-medium text-blue-700 hover:underline text-left">
                      Source: {doc.source}{doc.page ? `, page ${doc.page}` : ""}
                    </button>
                    <div className="text-blue-600/70 mt-0.5">Used {doc.passage_count} passage{doc.passage_count === 1 ? "" : "s"} from this page</div>
                    {doc.score !== undefined && <div className="text-blue-600/70 mt-0.5">Relevance: {doc.score}</div>}
                    {doc.passages?.slice(0, 2).map((passage: string, idx: number) => (
                      <div key={idx} className="mt-1 text-slate-600 line-clamp-3">"{passage}"</div>
                    ))}
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

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function markdownToPrintableHtml(content: string): string {
  const lines = content.split("\n");
  const html: string[] = [];
  let i = 0;
  const isTableSeparator = (line: string) => /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
  const isTableRow = (line: string) => line.trim().startsWith("|") && line.trim().endsWith("|");
  const splitCells = (line: string) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(cell => cell.trim());
  const inline = (text: string) => escapeHtml(text).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  while (i < lines.length) {
    if (isTableRow(lines[i]) && i + 1 < lines.length && isTableSeparator(lines[i + 1])) {
      const headers = splitCells(lines[i]);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && isTableRow(lines[i])) {
        rows.push(splitCells(lines[i]));
        i += 1;
      }
      html.push(`<table><thead><tr>${headers.map(h => `<th>${inline(h)}</th>`).join("")}</tr></thead><tbody>${rows.map(row => `<tr>${headers.map((_, idx) => `<td>${inline(row[idx] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
      continue;
    }
    const paragraph: string[] = [];
    while (i < lines.length && !(isTableRow(lines[i]) && i + 1 < lines.length && isTableSeparator(lines[i + 1]))) {
      if (lines[i].trim()) paragraph.push(lines[i]);
      i += 1;
    }
    if (paragraph.length) html.push(`<p>${inline(paragraph.join("\n")).replace(/\n/g, "<br/>")}</p>`);
  }
  return html.join("\n");
}

function buildSourcesHtml(sources: any): string {
  const docs = groupDocumentCitations(sources?.documents || []);
  const faq = sources?.faq || [];
  const db = sources?.database;
  const parts: string[] = [];
  if (docs.length) {
    parts.push(`<h2>Document sources</h2>${docs.map((doc: any) => `<div class="source"><strong>Source:</strong> ${escapeHtml(doc.source)}${doc.page ? `, page ${escapeHtml(doc.page)}` : ""}<br/><strong>Passages used:</strong> ${escapeHtml(doc.passage_count)}${doc.score !== undefined ? `<br/><strong>Best relevance:</strong> ${escapeHtml(doc.score)}` : ""}${(doc.passages || []).slice(0, 3).map((passage: string) => `<blockquote>${escapeHtml(passage)}</blockquote>`).join("")}</div>`).join("")}`);
  }
  if (db) {
    const source = (db.datasets || db.tables || ["Database"]).join(", ");
    parts.push(`<h2>Database source</h2><div class="source"><strong>Source:</strong> ${escapeHtml(source)}<br/><strong>Rows returned:</strong> ${escapeHtml(db.row_count ?? 0)}${db.sql ? `<details><summary>SQL</summary><pre>${escapeHtml(db.sql)}</pre></details>` : ""}</div>`);
  }
  if (faq.length) {
    parts.push(`<h2>FAQ sources</h2>${faq.map((item: any) => `<div class="source"><strong>${escapeHtml(item.question)}</strong><br/>${escapeHtml(item.answer)}</div>`).join("")}`);
  }
  return parts.join("\n") || "<p>No source evidence attached.</p>";
}

function buildChartRows(data: any) {
  const rows = Array.isArray(data?.result) ? data.result : [];
  if (!rows.length) return null;

  const cols = Object.keys(rows[0] || {});
  const numericCols = cols.filter(col => rows.some((row: any) => Number.isFinite(Number(row[col]))));
  const labelCol = cols.find(col => !numericCols.includes(col) && rows.some((row: any) => row[col])) || cols[0];
  const valueCol = numericCols.find(col => /score|rate|ratio|jobs|count|total|amount|value|percentage|percent/i.test(col)) || numericCols[0];
  if (!labelCol || !valueCol) return null;

  const chartRows: Array<{ label: string; value: number }> = rows
    .map((row: any) => ({ label: String(row[labelCol] ?? "-"), value: Number(row[valueCol]) }))
    .filter((row: any) => Number.isFinite(row.value))
    .slice(0, 8);
  if (chartRows.length < 2) return null;
  return { labelCol, valueCol, chartRows };
}

function buildChartHtml(data: any): string {
  const chart = buildChartRows(data);
  if (!chart) return "";
  const max = Math.max(...chart.chartRows.map((row: { label: string; value: number }) => Math.abs(row.value)), 1);
  const width = 720;
  const rowHeight = 34;
  const labelWidth = 210;
  const barWidth = 390;
  const height = 42 + chart.chartRows.length * rowHeight;
  const rows = chart.chartRows.map((row: { label: string; value: number }, idx: number) => {
    const y = 34 + idx * rowHeight;
    const w = Math.max(8, Math.round(Math.abs(row.value) / max * barWidth));
    return `<text x="0" y="${y + 13}" font-size="11" fill="#475569">${escapeHtml(row.label).slice(0, 34)}</text><rect x="${labelWidth}" y="${y}" width="${barWidth}" height="12" rx="6" fill="#f1f5f9"/><rect x="${labelWidth}" y="${y}" width="${w}" height="12" rx="6" fill="#ef4444"/><text x="${labelWidth + barWidth + 16}" y="${y + 11}" font-size="11" fill="#334155">${escapeHtml(row.value.toLocaleString(undefined, { maximumFractionDigits: 2 }))}</text>`;
  }).join("");
  return `<h2>Visual chart</h2><div class="chart"><svg viewBox="0 0 ${width} ${height}" width="100%" role="img" aria-label="Chart for ${escapeHtml(chart.valueCol)}"><text x="0" y="14" font-size="13" font-weight="700" fill="#334155">Quick chart: ${escapeHtml(chart.valueCol)}</text>${rows}</svg></div>`;
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

function escapeXml(value: unknown): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function crc32(bytes: Uint8Array): number {
  let crc = -1;
  for (const byte of bytes) {
    crc ^= byte;
    for (let i = 0; i < 8; i += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ -1) >>> 0;
}

function writeUint16(out: number[], value: number) {
  out.push(value & 255, (value >>> 8) & 255);
}

function writeUint32(out: number[], value: number) {
  out.push(value & 255, (value >>> 8) & 255, (value >>> 16) & 255, (value >>> 24) & 255);
}

function zipStored(files: Array<{ name: string; content: string }>): Blob {
  const encoder = new TextEncoder();
  const out: number[] = [];
  const central: number[] = [];
  const now = new Date();
  const dosTime = (now.getHours() << 11) | (now.getMinutes() << 5) | Math.floor(now.getSeconds() / 2);
  const dosDate = ((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate();

  for (const file of files) {
    const name = encoder.encode(file.name);
    const bytes = encoder.encode(file.content);
    const crc = crc32(bytes);
    const offset = out.length;

    writeUint32(out, 0x04034b50);
    writeUint16(out, 20);
    writeUint16(out, 0);
    writeUint16(out, 0);
    writeUint16(out, dosTime);
    writeUint16(out, dosDate);
    writeUint32(out, crc);
    writeUint32(out, bytes.length);
    writeUint32(out, bytes.length);
    writeUint16(out, name.length);
    writeUint16(out, 0);
    out.push(...name, ...bytes);

    writeUint32(central, 0x02014b50);
    writeUint16(central, 20);
    writeUint16(central, 20);
    writeUint16(central, 0);
    writeUint16(central, 0);
    writeUint16(central, dosTime);
    writeUint16(central, dosDate);
    writeUint32(central, crc);
    writeUint32(central, bytes.length);
    writeUint32(central, bytes.length);
    writeUint16(central, name.length);
    writeUint16(central, 0);
    writeUint16(central, 0);
    writeUint16(central, 0);
    writeUint16(central, 0);
    writeUint32(central, 0);
    writeUint32(central, offset);
    central.push(...name);
  }

  const centralOffset = out.length;
  out.push(...central);
  writeUint32(out, 0x06054b50);
  writeUint16(out, 0);
  writeUint16(out, 0);
  writeUint16(out, files.length);
  writeUint16(out, files.length);
  writeUint32(out, central.length);
  writeUint32(out, centralOffset);
  writeUint16(out, 0);

  return new Blob([new Uint8Array(out)], {
    type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  });
}

function docxParagraph(text: string, style?: "Title" | "Heading1") {
  const styleXml = style ? `<w:pPr><w:pStyle w:val="${style}"/></w:pPr>` : "";
  return `<w:p>${styleXml}<w:r><w:t xml:space="preserve">${escapeXml(text)}</w:t></w:r></w:p>`;
}

function buildDocxContent(content: string, sources: any): Blob {
  const paragraphs: string[] = [];
  paragraphs.push(docxParagraph(extractKeyAnswer(content), "Title"));
  paragraphs.push(docxParagraph(`Generated ${new Date().toLocaleString()} - ${sourceSummary(sources)}`));
  if (hasAiInsightContribution(content, sources)) paragraphs.push(docxParagraph("AI Insight contributed beyond strict source evidence."));
  paragraphs.push(docxParagraph("Answer", "Heading1"));
  for (const line of content.split("\n").map(item => item.trim()).filter(Boolean)) {
    if (!/^\|?\s*:?-{3,}/.test(line)) paragraphs.push(docxParagraph(line.replace(/\*\*/g, "")));
  }

  const chart = buildChartRows(sources?.database);
  if (chart) {
    paragraphs.push(docxParagraph("Visual chart", "Heading1"));
    paragraphs.push(...chart.chartRows.map(row => docxParagraph(`${row.label}: ${row.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`)));
  }

  paragraphs.push(docxParagraph("Sources and citations", "Heading1"));
  for (const doc of groupDocumentCitations(sources?.documents || [])) {
    paragraphs.push(docxParagraph(`Source: ${doc.source}${doc.page ? `, page ${doc.page}` : ""} - ${doc.passage_count} passage${doc.passage_count === 1 ? "" : "s"}`));
    for (const passage of (doc.passages || []).slice(0, 3)) paragraphs.push(docxParagraph(`Quote: ${passage}`));
  }
  const db = sources?.database;
  if (db) {
    paragraphs.push(docxParagraph(`Database source: ${(db.datasets || db.tables || ["Database"]).join(", ")}`));
    paragraphs.push(docxParagraph(`Rows returned: ${db.row_count ?? 0}`));
  }
  for (const item of sources?.faq || []) {
    paragraphs.push(docxParagraph(`FAQ: ${item.question}`));
    paragraphs.push(docxParagraph(item.answer));
  }

  const documentXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>${paragraphs.join("")}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>`;
  return zipStored([
    { name: "[Content_Types].xml", content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>` },
    { name: "_rels/.rels", content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>` },
    { name: "word/document.xml", content: documentXml },
  ]);
}

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function buildExportHtml(content: string, sources: any, options?: { memo?: boolean }) {
  const title = extractKeyAnswer(content);
  const generated = new Date().toLocaleString();
  const chartHtml = buildChartHtml(sources?.database);
  const aiBadge = hasAiInsightContribution(content, sources)
    ? `<span class="badge ai">AI Insight contributed</span>`
    : "";
  const memoIntro = options?.memo
    ? `<h2>Executive briefing</h2><p>This briefing summarizes the answer, available evidence, and recommended action for board or leadership review.</p>`
    : "";
  return `<!doctype html><html><head><meta charset="utf-8"/><title>${escapeHtml(options?.memo ? "ANDAI Executive Briefing" : "ANDAI Answer Export")}</title><style>
    body{font-family:Inter,Arial,sans-serif;color:#0f172a;margin:32px;line-height:1.55}.meta{color:#64748b;font-size:12px;margin-bottom:20px}.badge{display:inline-block;border:1px solid #a7f3d0;background:#ecfdf5;color:#047857;border-radius:999px;padding:3px 8px;font-size:12px;margin-right:6px}.badge.ai{border-color:#d8b4fe;background:#faf5ff;color:#7e22ce}h1{font-size:24px;margin:8px 0}h2{font-size:15px;margin:24px 0 8px;color:#334155}p{white-space:normal}table{width:100%;border-collapse:collapse;margin:14px 0;font-size:12px}th,td{border:1px solid #cbd5e1;padding:7px;text-align:left}th{background:#f1f5f9}.source,.chart{border:1px solid #e2e8f0;background:#f8fafc;border-radius:10px;padding:10px;margin:8px 0;font-size:12px}blockquote{border-left:3px solid #94a3b8;margin:8px 0 0;padding-left:10px;color:#475569}pre{white-space:pre-wrap;background:#fff;border:1px solid #e2e8f0;padding:8px;border-radius:8px}@media print{button{display:none}body{margin:18mm}.source,.chart{break-inside:avoid}}
  </style></head><body><button onclick="window.print()" style="float:right;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;background:white">Print / Save PDF</button><div><span class="badge">${escapeHtml(options?.memo ? "ANDAI executive briefing" : "ANDAI evidence report")}</span>${aiBadge}</div><h1>${escapeHtml(title)}</h1><div class="meta">Generated ${escapeHtml(generated)} · ${escapeHtml(sourceSummary(sources))}</div>${memoIntro}<h2>Answer</h2>${markdownToPrintableHtml(content)}${chartHtml}<h2>Sources and citations</h2>${buildSourcesHtml(sources)}<script>setTimeout(()=>window.print(),300)</script></body></html>`;
}

function exportAnswerPdf(content: string, sources: any) {
  const printable = window.open("", "_blank", "noopener,noreferrer,width=900,height=700");
  if (!printable) return;
  printable.document.write(buildExportHtml(content, sources));
  printable.document.close();
}

function exportBoardMemo(content: string, sources: any) {
  const printable = window.open("", "_blank", "noopener,noreferrer,width=900,height=700");
  if (!printable) return;
  printable.document.write(buildExportHtml(content, sources, { memo: true }));
  printable.document.close();
}

function exportAnswerWord(content: string, sources: any) {
  downloadBlob("andai-answer-report.docx", buildDocxContent(content, sources));
}

function extractKeyAnswer(content: string): string {
  const lines = content.split("\n").map(line => line.trim()).filter(Boolean);
  const firstText = lines.find(line => !line.startsWith("|") && !/^:?-{3,}/.test(line));
  return firstText?.replace(/^#+\s*/, "") || "Answer generated from selected sources";
}

function sourceSummary(sources: any) {
  const docs = sources?.documents?.length || 0;
  const docPages = groupDocumentCitations(sources?.documents || []).length;
  const faq = sources?.faq?.length || 0;
  const dbRows = sources?.database?.row_count ?? 0;
  const parts = [];
  if (dbRows) parts.push(`${dbRows} database row${dbRows === 1 ? "" : "s"}`);
  if (docs) parts.push(`${docs} PDF passage${docs === 1 ? "" : "s"} on ${docPages} page${docPages === 1 ? "" : "s"}`);
  if (faq) parts.push(`${faq} FAQ`);
  return parts.length ? parts.join(" · ") : "No source evidence attached";
}

function NumericResultChart({ data }: { data: any }) {
  const chart = buildChartRows(data);
  if (!chart) return null;

  const max = Math.max(...chart.chartRows.map((row: any) => Math.abs(row.value)), 1);
  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3">
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-slate-700">
        <BarChart3 size={14} className="text-red-500" /> Quick chart: {chart.valueCol}
      </div>
      <div className="space-y-2">
        {chart.chartRows.map((row: any, idx: number) => (
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

function hasAiInsightContribution(content: string, sources: any): boolean {
  if (sources?._meta?.ai_insight_contributed === true) return true;
  if (sources?._meta?.ai_insight_contributed === false) return false;
  return /^(insight|recommendation|recommended action|next step|why this matters)\s*:/im.test(content);
}

export function ExecutiveAnswerCard({ content, sources }: { content: string; sources: any }) {
  const hasSources = Boolean(sources?.database || sources?.documents?.length || sources?.faq?.length);
  const hasAiInsight = hasAiInsightContribution(content, sources);
  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white p-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Executive answer</div>
            <div className="mt-1 text-sm font-semibold text-slate-900">{extractKeyAnswer(content)}</div>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            <button
              type="button"
              onClick={() => navigator.clipboard?.writeText(content)}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-500 hover:bg-slate-50"
              title="Copy answer"
            >
              <Copy size={12} /> Copy
            </button>
            <button
              type="button"
              onClick={() => exportAnswerPdf(content, sources)}
              className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-[11px] font-medium text-red-600 hover:bg-red-100"
              title="Export answer as PDF"
            >
              <Download size={12} /> PDF
            </button>
            <button
              type="button"
              onClick={() => exportAnswerWord(content, sources)}
              className="inline-flex items-center gap-1 rounded-lg border border-blue-200 bg-blue-50 px-2 py-1 text-[11px] font-medium text-blue-600 hover:bg-blue-100"
              title="Export answer for Microsoft Word"
            >
              <FileText size={12} /> Word
            </button>
            <button
              type="button"
              onClick={() => exportBoardMemo(content, sources)}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-600 hover:bg-slate-50"
              title="Export board memo / executive briefing"
            >
              <BriefcaseBusiness size={12} /> Briefing
            </button>
          </div>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
          <span className={`rounded-full px-2 py-0.5 ${hasSources ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-slate-100 text-slate-500"}`}>
            {hasSources ? "Evidence-backed" : "No evidence attached"}
          </span>
          {hasAiInsight && (
            <span className="inline-flex items-center gap-1 rounded-full border border-purple-200 bg-purple-50 px-2 py-0.5 font-medium text-purple-700">
              <Lightbulb size={11} /> AI Insight added
            </span>
          )}
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
