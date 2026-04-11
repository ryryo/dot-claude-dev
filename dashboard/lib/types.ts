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
