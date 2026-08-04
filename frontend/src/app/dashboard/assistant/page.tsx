"use client";
import { useState, useEffect, useRef } from "react";
import { Send, Plus, Trash2, Bot, User, Database, FileText, HelpCircle, Loader2, Check, Lightbulb, Zap, Brain } from "lucide-react";
import { DatabaseResultTable, ExecutiveAnswerCard, SourceBadges } from "./components/MessageRenderers";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";
import { useAuth } from "@/lib/auth-context";
import { useI18n } from "@/lib/i18n-context";

const SOURCE_OPTIONS = [
  { key: "database", labelKey: "assistant.sourceDatabase", icon: Database, color: "emerald" },
  { key: "documents", labelKey: "assistant.sourceDocuments", icon: FileText, color: "blue" },
  { key: "faq", labelKey: "assistant.sourceFaq", icon: HelpCircle, color: "amber" },
] as const;

interface Session { id: number; title: string | null; department_ids?: number[]; created_at: string; message_count: number; }
interface Message { id: number; role: string; content: string; sources: any; sql_generated: string | null; created_at: string; model_tier?: string; response_time_ms?: number; }

export default function AssistantPage() {
  const { t } = useI18n();
  const companyId = useCompanyId();
  const { user } = useAuth();
  const chatDepartmentIds = user?.department_ids || [];
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [enabledSources, setEnabledSources] = useState<Set<string>>(new Set(["database", "documents", "faq"]));
  const [aiInsights, setAiInsights] = useState(false);
  const [modelMode, setModelMode] = useState<"auto" | "instant" | "thinking">("auto");
  const messagesEnd = useRef<HTMLDivElement>(null);

  const toggleSource = (key: string) => {
    setEnabledSources(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size > 1 || aiInsights) next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  useEffect(() => {
    loadSessions();
    setActiveSession(null);
    setMessages([]);
  }, [companyId]);
  useEffect(() => { messagesEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const loadSessions = async () => {
    try { const s = await api.getChatSessions(companyId ?? undefined); setSessions(s); } catch {}
  };

  const loadMessages = async (sessionId: number) => {
    setActiveSession(sessionId);
    try { const m = await api.getChatMessages(sessionId); setMessages(m); } catch {}
  };

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    const msg = input;
    setInput("");
    setSending(true);

    setMessages(prev => [...prev, { id: Date.now(), role: "user", content: msg, sources: null, sql_generated: null, created_at: new Date().toISOString() }]);

    try {
      const res = await api.sendMessage(
        msg,
        activeSession || undefined,
        companyId || undefined,
        Array.from(enabledSources),
        aiInsights,
        modelMode,
        chatDepartmentIds
      );
      if (!activeSession) {
        setActiveSession(res.session_id);
        await loadSessions();
      }
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, role: "assistant", content: res.message, sources: res.sources, sql_generated: null, created_at: new Date().toISOString(), model_tier: res.model_tier, response_time_ms: res.response_time_ms }
      ]);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, role: "assistant", content: `${t("assistant.errorPrefix")}: ${err.message}`, sources: null, sql_generated: null, created_at: new Date().toISOString() }
      ]);
    }
    setSending(false);
  };

  const newChat = () => { setActiveSession(null); setMessages([]); };

  const deleteChat = async (id: number) => {
    try {
      await api.deleteSession(id);
      if (activeSession === id) { setActiveSession(null); setMessages([]); }
      loadSessions();
    } catch {}
  };
  return (
    <div className="flex h-[calc(100vh-7.5rem)] flex-col gap-3 md:h-[calc(100vh-8rem)] md:flex-row md:gap-4">
      {/* Sessions sidebar */}
      <div className="h-36 w-full shrink-0 bg-white rounded-xl border border-slate-200 flex flex-col md:h-auto md:w-72">
        <div className="p-4 border-b border-slate-200">
          <button onClick={newChat} className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors">
            <Plus size={16} /> {t("assistant.newChat")}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((s) => (
            <div key={s.id} className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${activeSession === s.id ? "bg-red-50 border border-red-200" : "hover:bg-slate-50"}`}>
              <button onClick={() => loadMessages(s.id)} className="flex-1 text-left min-w-0">
                <p className="text-sm font-medium text-slate-700 truncate">{s.title || t("assistant.untitledChat")}</p>
                <p className="text-xs text-slate-400">{t("assistant.messageCount", { count: s.message_count })}</p>
              </button>
              <button onClick={() => deleteChat(s.id)} aria-label={t("assistant.deleteChat")} title={t("assistant.deleteChat")} className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 transition-all">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <div className="text-center py-8 text-slate-400 text-sm">{t("assistant.noConversations")}</div>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="min-h-0 flex-1 bg-white rounded-xl border border-slate-200 flex flex-col">
        <div className="flex-1 overflow-y-auto p-3 space-y-4 md:p-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <Bot size={48} className="mb-4 text-slate-300" />
              <p className="text-lg font-medium">{t("assistant.welcome")}</p>
              <p className="text-sm mt-1">{t("assistant.welcomeCopy")}</p>
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                  <Bot size={16} className="text-red-600" />
                </div>
              )}
              <div className={`max-w-[75%] ${msg.role === "user" ? "bg-red-600 text-white rounded-2xl rounded-br-md px-4 py-3" : "bg-slate-50 rounded-2xl rounded-bl-md px-4 py-3"}`}>
                {msg.role === "assistant" ? (
                  <ExecutiveAnswerCard content={msg.content} sources={msg.sources} />
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                )}

                {msg.role === "assistant" && msg.sources?.database && (
                  <DatabaseResultTable data={msg.sources.database} />
                )}

                {msg.role === "assistant" && <SourceBadges sources={msg.sources} />}
                {msg.role === "assistant" && (msg.model_tier || msg.response_time_ms) && (
                  <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-400">
                    {msg.model_tier === "instant" && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600 border border-emerald-200">
                        <Zap size={9} /> {t("assistant.instant")}
                      </span>
                    )}
                    {msg.model_tier === "thinking" && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-violet-50 text-violet-600 border border-violet-200">
                        <Brain size={9} /> {t("assistant.thinking")}
                      </span>
                    )}
                    {msg.response_time_ms && (
                      <span>{(msg.response_time_ms / 1000).toFixed(1)}s</span>
                    )}
                  </div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center">
                  <User size={16} className="text-slate-600" />
                </div>
              )}
            </div>
          ))}
          {sending && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                <Bot size={16} className="text-red-600" />
              </div>
              <div className="bg-slate-50 rounded-2xl rounded-bl-md px-4 py-3">
                <Loader2 size={18} className="animate-spin text-slate-400" />
              </div>
            </div>
          )}
          <div ref={messagesEnd} />
        </div>

        <div className="px-4 pt-3 pb-1 border-t border-slate-200">
          <div className="flex items-center gap-1.5 mb-2 flex-wrap">
            <span className="text-xs font-medium text-slate-500 mr-1">{t("assistant.searchIn")}</span>
            {SOURCE_OPTIONS.map(({ key, labelKey, icon: Icon, color }) => {
              const active = enabledSources.has(key);
              const colorMap: Record<string, { bg: string; border: string; text: string; activeBg: string; activeBorder: string; activeText: string }> = {
                emerald: { bg: "bg-white", border: "border-slate-200", text: "text-slate-400", activeBg: "bg-emerald-50", activeBorder: "border-emerald-300", activeText: "text-emerald-700" },
                blue:    { bg: "bg-white", border: "border-slate-200", text: "text-slate-400", activeBg: "bg-blue-50",    activeBorder: "border-blue-300",    activeText: "text-blue-700" },
                amber:   { bg: "bg-white", border: "border-slate-200", text: "text-slate-400", activeBg: "bg-amber-50",   activeBorder: "border-amber-300",   activeText: "text-amber-700" },
              };
              const c = colorMap[color];
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => toggleSource(key)}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    active
                      ? `${c.activeBg} ${c.activeBorder} ${c.activeText}`
                      : `${c.bg} ${c.border} ${c.text} hover:border-slate-300`
                  }`}
                >
                  {active && <Check size={12} strokeWidth={3} />}
                  <Icon size={12} />
                  {t(labelKey)}
                </button>
              );
            })}
            <div className="w-px h-5 bg-slate-200 mx-1" />
            <button
              type="button"
              onClick={() => {
                const next = !aiInsights;
                setAiInsights(next);
                if (!next && enabledSources.size === 0) {
                  setEnabledSources(new Set(["database", "documents", "faq"]));
                }
              }}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                aiInsights
                  ? "bg-purple-50 border-purple-300 text-purple-700"
                  : "bg-white border-slate-200 text-slate-400 hover:border-slate-300"
              }`}
            >
              {aiInsights && <Check size={12} strokeWidth={3} />}
              <Lightbulb size={12} />
              {aiInsights ? (enabledSources.size === 0 ? t("assistant.aiOnly") : t("assistant.aiInsights")) : t("assistant.sourceOnly")}
            </button>
          </div>
          {!aiInsights && (
            <div className="mb-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-[11px] text-blue-700">
              {t("assistant.sourceOnlyCopy")}
            </div>
          )}
          <div className="mb-2 flex items-center gap-2 text-[11px] flex-wrap">
            <span className="text-slate-400">{t("assistant.responseMode")}</span>
            <button
              type="button"
              onClick={() => setModelMode("auto")}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${
                modelMode === "auto"
                  ? "bg-slate-100 text-slate-700 border-slate-300"
                  : "bg-white text-slate-400 border-slate-200"
              }`}
            >
              {t("assistant.auto")}
            </button>
            <button
              type="button"
              onClick={() => setModelMode("instant")}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${
                modelMode === "instant"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                  : "bg-white text-slate-400 border-slate-200"
              }`}
            >
              <Zap size={10} />
              {t("assistant.quick")}
            </button>
            <button
              type="button"
              onClick={() => setModelMode("thinking")}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border ${
                modelMode === "thinking"
                  ? "bg-violet-50 text-violet-700 border-violet-300"
                  : "bg-white text-slate-400 border-slate-200"
              }`}
            >
              <Brain size={10} />
              {t("assistant.deep")}
            </button>
          </div>
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder={t("assistant.placeholder")}
              className="flex-1 px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent text-sm"
              disabled={sending}
            />
            <button
              onClick={handleSend}
              aria-label={t("assistant.send")}
              title={t("assistant.send")}
              disabled={sending || !input.trim()}
              className="px-4 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50"
            >
              <Send size={18} />
            </button>
          </div>
          {chatDepartmentIds.length === 0 && (
            <p className="mt-2 text-xs text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
              {t("assistant.noDepartment")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
