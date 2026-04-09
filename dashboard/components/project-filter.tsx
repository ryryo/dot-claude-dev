"use client"

import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import type { ProjectConfig } from "@/lib/types"
import { cn } from "@/lib/utils"

interface ProjectFilterProps {
  projects: ProjectConfig[]
  selected: string[]
  onToggle: (name: string) => void
  planCounts: Record<string, number>
}

export function ProjectFilter({
  projects,
  selected,
  onToggle,
  planCounts,
}: ProjectFilterProps) {
  const selectedSet = new Set(selected)
  const selectedCount = projects.filter((project) => selectedSet.has(project.name)).length
  const allSelected = projects.length > 0 && selectedCount === projects.length

  const handleToggleAll = () => {
    const targetProjects = allSelected
      ? projects.filter((project) => selectedSet.has(project.name))
      : projects.filter((project) => !selectedSet.has(project.name))

    targetProjects.forEach((project) => onToggle(project.name))
  }

  return (
    <nav aria-label="プロジェクトフィルター" className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <h3 className="text-sm font-semibold">プロジェクトフィルター</h3>
          <p className="text-muted-foreground text-xs">
            {selectedCount}/{projects.length} 件を表示対象にしています。
          </p>
        </div>

        <button
          type="button"
          onClick={handleToggleAll}
          className="text-label text-primary min-h-[44px] px-2 transition-opacity hover:opacity-80"
        >
          {allSelected ? "すべて解除" : "すべて選択"}
        </button>
      </div>

      <ul className="space-y-2" role="list">
        {projects.map((project) => {
          const isSelected = selectedSet.has(project.name)

          return (
            <li key={project.name}>
            <button
              type="button"
              onClick={() => onToggle(project.name)}
              className={cn(
                "flex w-full items-start justify-between gap-3 rounded-lg border p-3 text-left transition-colors cursor-pointer",
                isSelected ? "bg-accent/50" : "bg-background hover:bg-muted/60"
              )}
              aria-pressed={isSelected}
            >
              <div className="flex min-w-0 items-start gap-3">
                <Checkbox checked={isSelected} className="pointer-events-none mt-0.5" aria-hidden="true" />
                <div className="min-w-0 space-y-1">
                  <p className="truncate text-sm font-medium">{project.name}</p>
                  <p className="text-muted-foreground truncate text-xs" title={project.repo}>
                    {project.repo}
                  </p>
                </div>
              </div>

              <Badge variant="secondary" className="shrink-0 tabular-nums">
                {planCounts[project.name] ?? 0} PLAN
              </Badge>
            </button>
            </li>
          )
        })}

        {projects.length === 0 ? (
          <li className="list-none">
          <div className="text-muted-foreground rounded-xl border border-dashed px-3 py-6 text-center text-sm">
            プロジェクトが見つかりません。
          </div>
          </li>
        ) : null}
      </ul>
    </nav>
  )
}
