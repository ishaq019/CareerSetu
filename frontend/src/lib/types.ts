// Shared API response types mirroring the backend Pydantic schemas.

export type User = { id: number; email: string };

export type TokenResponse = { access_token: string; token_type: string; user: User };

export type SkillResult = {
  skill: string;
  required_level: string;
  detected_level: string;
  status: string; // strong | partial | missing
  evidence: string;
};

export type RoadmapStep = {
  skill: string;
  target_level: string;
  priority: string;
  steps: string[];
};

export type Analysis = {
  id: number | null;
  match_score: number;
  ats_coverage: number;
  recommendation: "STRONG_MATCH" | "MATCH_WITH_IMPROVEMENTS" | "LOW_MATCH" | string;
  summary: string;
  strengths: SkillResult[];
  gaps: SkillResult[];
  roadmap: RoadmapStep[];
};

export type HistoryItem = {
  id: number;
  title: string;
  match_score: number;
  ats_coverage: number;
  recommendation: string;
  summary: string;
  created_at: string;
};

export type HistoryDetail = HistoryItem & {
  result: Analysis;
  resume_text: string;
  job_description: string;
};

export type ParseResult = {
  filename: string;
  characters: number;
  text: string;
  ai_insight?: unknown;
};

export type ChatSource = {
  text: string;
  source: string;
  page: number | null;
  score: number;
  citation: number;
};
export type ChatResponse = {
  answer: string;
  confidence: "high" | "medium" | "low" | string;
  sources: ChatSource[];
};

export type InterviewQuestion = { question: string; topic: string; difficulty: string };
export type Evaluation = {
  id: number | null;
  score: number;
  strengths: string[];
  improvements: string[];
  evidence_quality: string;
  next_difficulty: string;
};
export type InterviewAttempt = Evaluation & { question: string; created_at: string };

export type ResumeDraft = {
  summary: string;
  skills: string[];
  experience_bullets: string[];
  project_bullets: string[];
  ats_keywords: string[];
};

export type CoverLetterDraft = {
  greeting: string;
  opening: string;
  body: string[];
  closing: string;
  signature: string;
};

export type RoadmapDoc = { items: any[] };
