export type PlanStatus = 'not-started' | 'in-progress' | 'in-review' | 'completed';

export interface TodoItem {
  title: string;
  checked: boolean;
  hasReview: boolean;
  reviewFilled: boolean;
}

export interface Gate {
  id: string;
  title: string;
  todos: TodoItem[];
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
  todos: TodoItem[];
  progress: {
    total: number;
    completed: number;
    percentage: number;
  };
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
