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
  path: string;
}

export interface ProjectsConfig {
  projects: ProjectConfig[];
}
