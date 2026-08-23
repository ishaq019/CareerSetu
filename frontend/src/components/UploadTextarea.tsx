// A textarea with an attached "Upload PDF/DOCX" control that calls the backend
// /documents/parse endpoint and fills the field with the extracted text.
import { useState } from "react";
import { Upload } from "lucide-react";
import { api } from "../lib/api";
import type { ParseResult } from "../lib/types";
import { Field, Spinner, Textarea } from "./ui";

export function UploadTextarea({
  label,
  hint,
  value,
  onChange,
  placeholder,
  rows = 8,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  rows?: number;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function onFile(file?: File) {
    if (!file) return;
    setErr("");
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", file);
      // Guest-safe: parse works without auth.
      const res = await api.post<ParseResult>("/documents/parse", form, { auth: false });
      onChange(res.text);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not read that document.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Field label={label} hint={hint}>
      <Textarea
        value={value}
        rows={rows}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="upload-row">
        <label className="upload">
          {busy ? <Spinner /> : <Upload size={13} />} Upload PDF/DOCX
          <input
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            disabled={busy}
            onChange={(e) => onFile(e.target.files?.[0])}
          />
        </label>
        <span className="muted" style={{ fontSize: 12, fontFamily: "var(--font-mono)" }}>
          {value.trim().length} chars
        </span>
      </div>
      {err && (
        <div className="alert alert-error" role="alert" style={{ marginTop: 4 }}>
          {err}
        </div>
      )}
    </Field>
  );
}
