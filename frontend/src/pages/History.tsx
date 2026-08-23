// Saved analyses: list, open a detail view (reusing AnalysisView), and delete.
import { useEffect, useState } from "react";
import { ArrowLeft, History as HistoryIcon, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import type { HistoryDetail, HistoryItem } from "../lib/types";
import { Page } from "../components/AppLayout";
import { AnalysisView, recLabel } from "../components/AnalysisView";
import { Badge, Button, Card, EmptyState } from "../components/ui";

function fmt(d: string) {
  return new Date(d).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function History() {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [detail, setDetail] = useState<HistoryDetail | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  function load() {
    api.get<HistoryItem[]>("/analysis/history").then(setItems).catch(() => setItems([]));
  }
  useEffect(load, []);

  async function open(id: number) {
    const d = await api.get<HistoryDetail>(`/analysis/history/${id}`);
    setDetail(d);
  }

  async function remove(id: number) {
    setBusy(id);
    try {
      await api.del(`/analysis/history/${id}`);
      setItems((prev) => (prev ? prev.filter((i) => i.id !== id) : prev));
      if (detail?.id === id) setDetail(null);
    } finally {
      setBusy(null);
    }
  }

  if (detail) {
    return (
      <Page
        title="Saved analysis"
        subtitle={fmt(detail.created_at)}
        actions={
          <Button variant="ghost" onClick={() => setDetail(null)}>
            <ArrowLeft size={15} /> Back to list
          </Button>
        }
      >
        <AnalysisView a={detail.result} />
      </Page>
    );
  }

  return (
    <Page title="Saved analyses" subtitle="Reopen a past report or remove it.">
      <Card>
        {items === null ? (
          <div className="center-load" style={{ minHeight: 200 }}>
            <span className="spinner" style={{ borderTopColor: "var(--a1)" }} /> Loading…
          </div>
        ) : items.length === 0 ? (
          <EmptyState icon={<HistoryIcon size={22} />} title="No saved analyses yet">
            Run a job-fit analysis and keep “Save to my history” checked.
          </EmptyState>
        ) : (
          items.map((it) => {
            const rec = recLabel(it.recommendation);
            return (
              <div className="list-row" key={it.id}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                    <strong style={{ fontFamily: "var(--font-mono)" }}>{it.match_score}</strong>
                    <Badge tone={rec.tone}>{rec.text}</Badge>
                    <span className="muted" style={{ fontSize: 12.5 }}>{fmt(it.created_at)}</span>
                  </div>
                  <p className="muted" style={{ fontSize: 13, marginTop: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "60ch" }}>
                    {it.summary}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8, flex: "none" }}>
                  <Button variant="ghost" onClick={() => open(it.id)}>
                    View
                  </Button>
                  <Button variant="danger" loading={busy === it.id} onClick={() => remove(it.id)} aria-label="Delete">
                    <Trash2 size={15} />
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </Card>
    </Page>
  );
}
