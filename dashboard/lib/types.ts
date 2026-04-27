export type PlanStatus = 'not-started' | 'in-progress' | 'in-review' | 'completed';
export type ReviewResult = 'PASSED' | 'FAILED' | 'SKIPPED' | 'IN_PROGRESS';

// ===== 正規化 PlanFile (v3 ベース) =====

export interface AcceptanceCriteria {
  id: string;
  description: string;
  checked: boolean;
}

export interface AffectedFile {
  path: string;
  operation: 'create' | 'modify' | 'delete' | string;
  summary: string;
}

export interface Todo {
  id: string;
  gate: string;
  title: string;
  tdd: boolean;
  dependencies: string[];
  affectedFiles: AffectedFile[];
}

export interface GateReview {
  result: ReviewResult;
  fixCount: number;
  summary: string;
}

export interface Gate {
  id: string;
  title: string;
  summary: string;
  dependencies: string[];
  goal: { what: string; why: string };
  constraints: { must: string[]; mustNot: string[] };
  acceptanceCriteria: AcceptanceCriteria[];
  todos: Todo[];
  review: GateReview | null;
  passed: boolean;
}

export interface PlanProgress {
  gatesPassed: number;
  gatesTotal: number;
  currentGate: string | null;
  currentGateAC: { passed: number; total: number };
}

export interface PlanFile {
  filePath: string;
  fileName: string;
  projectName: string;
  title: string;
  createdDate: string | null;
  reviewChecked: boolean;
  status: PlanStatus;
  gates: Gate[];
  progress: PlanProgress;
  summary: string;
  rawMarkdown: string;
}

export interface ProjectConfig {
  name: string;
  repo: string;
}

export interface GitHubRepo {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  description: string | null;
  updated_at: string;
  html_url: string;
  default_branch: string;
}

export interface GitHubContent {
  name: string;
  path: string;
  type: 'file' | 'dir';
  sha: string;
}

export interface RepoError {
  repo: string;
  message: string;
}

export interface ProjectsConfig {
  projects: ProjectConfig[];
}

// ===== tasks.json schema v3 =====

export interface TasksJsonV3Spec {
  slug: string;
  title: string;
  summary: string;
  createdDate: string;
  specPath: string;
}

export interface TasksJsonV3Progress {
  gatesPassed: number;
  gatesTotal: number;
  currentGate: string | null;
  currentGateAC: { passed: number; total: number };
}

export interface TasksJsonV3Preflight {
  id: string;
  title: string;
  command: string;
  manual: boolean;
  reason: string;
  ac: string;
  checked: boolean;
}

export interface TasksJsonV3AcceptanceCriteria {
  id: string;
  description: string;
  checked: boolean;
}

export interface TasksJsonV3AffectedFile {
  path: string;
  operation: string;
  summary: string;
}

export interface TasksJsonV3Todo {
  id: string;
  gate: string;
  title: string;
  tdd: boolean;
  dependencies: string[];
  affectedFiles: TasksJsonV3AffectedFile[];
}

export interface TasksJsonV3Review {
  result: ReviewResult;
  fixCount: number;
  summary: string;
}

export interface TasksJsonV3Gate {
  id: string;
  title: string;
  summary: string;
  dependencies: string[];
  goal: { what: string; why: string };
  constraints: { must: string[]; mustNot: string[] };
  acceptanceCriteria: TasksJsonV3AcceptanceCriteria[];
  todos: TasksJsonV3Todo[];
  review: TasksJsonV3Review | null;
  passed: boolean;
}

export interface TasksJsonV3Metadata {
  createdAt: string;
  totalGates: number;
  totalTodos: number;
}

export interface TasksJsonV3 {
  schemaVersion: 3;
  spec: TasksJsonV3Spec;
  status: PlanStatus;
  reviewChecked: boolean;
  progress: TasksJsonV3Progress;
  preflight: TasksJsonV3Preflight[];
  gates: TasksJsonV3Gate[];
  metadata: TasksJsonV3Metadata;
}
