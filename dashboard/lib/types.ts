export type PlanStatus = 'not-started' | 'in-progress' | 'in-review' | 'completed';
export type StepKind = 'impl' | 'review';
export type ReviewResult = 'PASSED' | 'FAILED' | 'SKIPPED' | 'IN_PROGRESS';

export interface Step {
  title: string;
  checked: boolean;
  kind: StepKind;
  description: string;
  hasReview: boolean;
  reviewFilled: boolean;
  reviewResult: ReviewResult | null;
  reviewFixCount: number | null;
}

export interface Todo {
  title: string;
  steps: Step[];
}

export interface Gate {
  id: string;
  title: string;
  todos: Todo[];
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
  todos: Todo[];
  progress: {
    total: number;
    completed: number;
    percentage: number;
  };
  summary: string;
  rawMarkdown: string;
  hasV2Tasks: boolean;
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

// ===== tasks.json schema v2 =====

export interface TasksJsonV2Spec {
  slug: string;
  title: string;
  summary: string;
  createdDate: string; // YYYY-MM-DD
  specPath: string; // 通常 'spec.md'
}

export interface TasksJsonV2Progress {
  completed: number;
  total: number;
}

export interface TasksJsonV2Preflight {
  id: string;
  title: string;
  command: string;
  manual: boolean;
  reason: string;
}

export interface TasksJsonV2Gate {
  id: string;
  title: string;
  description: string;
  dependencies: string[];
  passCondition: string;
}

export interface TasksJsonV2AffectedFile {
  path: string;
  operation: string; // create | modify | delete 等
  summary: string;
}

export interface TasksJsonV2Review {
  result: ReviewResult;
  fixCount: number;
  summary: string;
}

export interface TasksJsonV2Step {
  kind: StepKind;
  title: string;
  checked: boolean;
  review?: TasksJsonV2Review | null;
}

export interface TasksJsonV2Todo {
  id: string;
  gate: string;
  title: string;
  description: string;
  tdd: boolean;
  dependencies: string[];
  affectedFiles: TasksJsonV2AffectedFile[];
  impl: string;
  relatedIssues: string[];
  steps: TasksJsonV2Step[];
}

export interface TasksJsonV2Metadata {
  createdAt: string;
  totalGates: number;
  totalTodos: number;
}

export interface TasksJsonV2 {
  schemaVersion: 2;
  spec: TasksJsonV2Spec;
  status: PlanStatus;
  reviewChecked: boolean;
  progress: TasksJsonV2Progress;
  preflight: TasksJsonV2Preflight[];
  gates: TasksJsonV2Gate[];
  todos: TasksJsonV2Todo[];
  metadata: TasksJsonV2Metadata;
}
