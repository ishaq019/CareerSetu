// Grounded career chat: retrieve-then-answer with visible citations. Handles
// the 503 (no LLM / empty knowledge base) case with a clear message.
import { useRef, useState } from "react";
import { MessageSquare, Send } from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { ChatResponse } from "../lib/types";
import { Page } from "../components/AppLayout";
import { Badge, Button, Card, EmptyState, Input } from "../components/ui";

type Msg =
  | { role: "user"; text: string }
  | { role: "bot"; text: string; confidence?: string; sources?: ChatResponse["sources"] };

export default function Chat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  function scroll() {
    setTimeout(() => logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: "smooth" }), 40);
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (question.length < 3 || busy) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setBusy(true);
    scroll();
    try {
      const res = await api.post<ChatResponse>("/chat", { question });
      setMessages((m) => [
        ...m,
        { role: "bot", text: res.answer, confidence: res.confidence, sources: res.sources },
      ]);
    } catch (err) {
      const msg =
        err instanceof ApiError && err.status === 503
          ? "Chat needs a configured LLM provider and an ingested knowledge base."
          : err instanceof Error
            ? err.message
            : "Something went wrong.";
      setMessages((m) => [...m, { role: "bot", text: msg }]);
    } finally {
      setBusy(false);
      scroll();
    }
  }

  return (
    <Page title="Career chat" subtitle="Answers are grounded in — and cite — the knowledge base.">
      <Card>
        <div className="chat-log" ref={logRef} style={{ maxHeight: "56vh", overflowY: "auto" }}>
          {messages.length === 0 && (
            <EmptyState icon={<MessageSquare size={22} />} title="Ask a career question">
              e.g. “How should I structure a system design answer?”
            </EmptyState>
          )}
          {messages.map((m, i) =>
            m.role === "user" ? (
              <div className="msg user" key={i}>
                {m.text}
              </div>
            ) : (
              <div className="msg bot" key={i}>
                {m.confidence && (
                  <div style={{ marginBottom: 8 }}>
                    <Badge tone={m.confidence === "high" ? "good" : m.confidence === "low" ? "bad" : "warn"}>
                      {m.confidence} confidence
                    </Badge>
                  </div>
                )}
                {m.text}
                {m.sources && m.sources.length > 0 && (
                  <div className="cites">
                    {m.sources.map((s) => (
                      <div className="cite" key={s.citation}>
                        [{s.citation}] {s.source}
                        {s.page ? `, p.${s.page}` : ""}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ),
          )}
          {busy && (
            <div className="msg bot">
              <span className="spinner" style={{ borderTopColor: "var(--a1)" }} />
            </div>
          )}
        </div>

        <form className="composer" onSubmit={send}>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about interviews, resumes, or a skill…"
          />
          <Button type="submit" loading={busy} disabled={input.trim().length < 3}>
            <Send size={15} />
          </Button>
        </form>
      </Card>
    </Page>
  );
}
