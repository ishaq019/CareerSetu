// Learning roadmap: generate a plan from skills (LLM with offline fallback),
// review it, and save one plan per user. Loads any saved plan on mount.
import { useEffect, useMemo, useState } from "react";
import { Check, Map as MapIcon, Plus, Save, X } from "lucide-react";
import { api, ApiError } from "../lib/api";
import type { RoadmapDoc } from "../lib/types";
import { Page } from "../components/AppLayout";
import { Badge, Button, Card, EmptyState, ErrorAlert, Input } from "../components/ui";

type Item = {
  skill?: string;
  levels?: string[];
  status?: string;
  steps?: string[];
  [k: string]: unknown;
};

export default function Roadmap() {
  const [skills, setSkills] = useState<string[]>([]);
  const [draftSkill, setDraftSkill] = useState("");
  const [items, setItems] = useState<Item[]>([]);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<RoadmapDoc>("/roadmap")
      .then((d) => setItems((d.items as Item[]) || []))
      .catch(() => setItems([]));
  }, []);

  function addSkill() {
    const parts = draftSkill
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (!parts.length) return;
    setSkills((prev) => Array.from(new Set([...prev, ...parts])).slice(0, 20));
    setDraftSkill("");
  }

  async function generate() {
    if (!skills.length) {
      setError("Add at least one skill to build a roadmap.");
      return;
    }
    setError("");
    setSavedAt(false);
    setBusy(true);
    try {
      const res = await api.post<RoadmapDoc>("/roadmap/generate", { skills });
      setItems((res.items as Item[]) || []);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not generate a roadmap.");
    } finally {
      setBusy(false);
    }
  }

  async function save() {
    setSaving(true);
    setError("");
    try {
      await api.post<RoadmapDoc>("/roadmap", { items });
      setSavedAt(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not save the roadmap.");
    } finally {
      setSaving(false);
    }
  }

  const hasItems = useMemo(() => items && items.length > 0, [items]);

  return (
    <Page
      title="Learning roadmap"
      subtitle="Turn skill gaps into a plan and save it to your account."
      actions={
        hasItems ? (
          <Button variant="ghost" loading={saving} onClick={save}>
            {savedAt ? <Check size={15} /> : <Save size={15} />} {savedAt ? "Saved" : "Save roadmap"}
          </Button>
        ) : undefined
      }
    >
      <div className="stack" style={{ gap: 18 }}>
        <Card>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-end", flexWrap: "wrap" }}>
            <div className="field" style={{ flex: 1, minWidth: 220 }}>
              <label>Skills to learn</label>
              <Input
                value={draftSkill}
                onChange={(e) => setDraftSkill(e.target.value)}
                onKeyDown={(e) => (e.key === "Enter" ? (e.preventDefault(), addSkill()) : undefined)}
                placeholder="e.g. Docker, Kubernetes, GraphQL"
              />
            </div>
            <Button variant="ghost" onClick={addSkill}>
              <Plus size={15} /> Add
            </Button>
            <Button loading={busy} onClick={generate}>
              Generate roadmap
            </Button>
          </div>
          {skills.length > 0 && (
            <div className="tag-wrap" style={{ marginTop: 14 }}>
              {skills.map((s) => (
                <button
                  key={s}
                  className="badge"
                  onClick={() => setSkills((prev) => prev.filter((x) => x !== s))}
                  style={{ cursor: "pointer", border: "none" }}
                  title="Remove"
                >
                  {s} <X size={12} />
                </button>
              ))}
            </div>
          )}
          {error && (
            <div style={{ marginTop: 14 }}>
              <ErrorAlert>{error}</ErrorAlert>
            </div>
          )}
        </Card>

        {!hasItems ? (
          <Card>
            <EmptyState icon={<MapIcon size={22} />} title="No roadmap yet">
              Add the skills you want to grow, then generate a plan.
            </EmptyState>
          </Card>
        ) : (
          <div className="two-col">
            {items.map((it, i) => (
              <Card key={(it.skill as string) || i}>
                <div className="card-h">
                  <h3>{it.skill || `Item ${i + 1}`}</h3>
                  {it.status && <Badge>{String(it.status).replace("_", " ")}</Badge>}
                </div>
                {Array.isArray(it.levels) && it.levels.length > 0 && (
                  <div className="tag-wrap" style={{ marginBottom: 12 }}>
                    {it.levels.map((l) => (
                      <Badge tone="warn" key={String(l)}>
                        {String(l)}
                      </Badge>
                    ))}
                  </div>
                )}
                {Array.isArray(it.steps) && (
                  <ul className="pill-list good">
                    {it.steps.map((step, j) => (
                      <li key={j}>{String(step)}</li>
                    ))}
                  </ul>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </Page>
  );
}
