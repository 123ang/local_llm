"use client";
import { useState, useEffect, useRef } from "react";
import { Send, Plus, Trash2, Bot, User, FileText, HelpCircle, Loader2, Check, Zap } from "lucide-react";
import { ExecutiveAnswerCard, SourceBadges } from "./components/MessageRenderers";
import { api } from "@/lib/api";
import { useCompanyId } from "@/hooks/useCompanyId";

const SOURCE_OPTIONS = [
  { key: "documents", label: "Policy Docs", icon: FileText, color: "blue" },
  { key: "faq", label: "FAQ", icon: HelpCircle, color: "amber" },
] as const;

interface Session { id: number; title: string | null; created_at: string; message_count: number; }
interface Message { id: number; role: string; content: string; sources: any; sql_generated: string | null; created_at: string; model_tier?: string; response_time_ms?: number; }

export default function AssistantPage() {
  const companyId = useCompanyId();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [enabledSources, setEnabledSources] = useState<Set<string>>(new Set(["documents", "faq"]));
  const messagesEnd = useRef<HTMLDivElement>(null);

  const toggleSource = (key: string) => {
    setEnabledSources(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size > 1) next.delete(key);
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
        false,
        "instant"
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
        { id: Date.now() + 1, role: "assistant", content: `Error: ${err.message}`, sources: null, sql_generated: null, created_at: new Date().toISOString() }
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
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Sessions sidebar */}
      <div className="w-72 bg-white rounded-xl border border-slate-200 flex flex-col">
        <div className="p-4 border-b border-slate-200">
          <button onClick={newChat} className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors">
            <Plus size={16} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.map((s) => (
            <div key={s.id} className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${activeSession === s.id ? "bg-red-50 border border-red-200" : "hover:bg-slate-50"}`}>
              <button onClick={() => loadMessages(s.id)} className="flex-1 text-left min-w-0">
                <p className="text-sm font-medium text-slate-700 truncate">{s.title || "New chat"}</p>
                <p className="text-xs text-slate-400">{s.message_count} messages</p>
              </button>
              <button onClick={() => deleteChat(s.id)} className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 transition-all">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {sessions.length === 0 && (
            <div className="text-center py-8 text-slate-400 text-sm">No conversations yet</div>
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 bg-white rounded-xl border border-slate-200 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-slate-400">
              <Bot size={48} className="mb-4 text-slate-300" />
              <p className="text-lg font-medium">Techpedia AI Assistant</p>
              <p className="text-sm mt-1">Ask about approved policy documents and published FAQ entries.</p>
              <div className="mt-6 w-full max-w-xl">
                <p className="text-xs font-medium text-slate-500 mb-2">Try asking:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {[
                    "What is the eligibility requirement for SME financing?",
                    "Which policy section covers credit assessment?",
                    "What documents are required before approval?",
                    "Summarize the procedure for reviewing an application.",
                    "Where can I find the exception handling rule?",
                  ].map((q) => (
                    <button
                      key={q}
                      type="button"
                      onClick={() => setInput(q)}
                      className="px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs text-left transition-colors border border-slate-200"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
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

                {msg.role === "assistant" && <SourceBadges sources={msg.sources} />}
                {msg.role === "assistant" && (msg.model_tier || msg.response_time_ms) && (
                  <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-400">
                    {msg.model_tier === "instant" && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-600 border border-emerald-200">
                        <Zap size={9} /> Instant
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
            <span className="text-xs font-medium text-slate-500 mr-1">Search in:</span>
            {SOURCE_OPTIONS.map(({ key, label, icon: Icon, color }) => {
              const active = enabledSources.has(key);
              const colorMap: Record<string, { bg: string; border: string; text: string; activeBg: string; activeBorder: string; activeText: string }> = {
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
                  {label}
                </button>
              );
            })}
          </div>
          <div className="mb-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-[11px] text-blue-700">
            Source-only mode is enforced: Techpedia AI Assistant answers only from selected policy documents or FAQ evidence.
          </div>
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder="Ask about SME policy, procedure, or FAQ..."
              className="flex-1 px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent text-sm"
              disabled={sending}
            />
            <button
              onClick={handleSend}
              disabled={sending || !input.trim()}
              className="px-4 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
