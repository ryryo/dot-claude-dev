"use client"

import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import type { GitHubRepo } from "@/lib/types"

interface RepoSelectorProps {
  repos: GitHubRepo[]
  selected: string[]
  onToggle: (fullName: string) => void
  planCounts: Record<string, number>
  errorRepos: string[]
}

export function RepoSelector({
  repos,
  selected,
  onToggle,
  planCounts,
  errorRepos,
}: RepoSelectorProps) {
  return (
    <div className="space-y-1">
      <p className="text-label mb-2 font-medium text-muted-foreground">リポジトリ</p>
      {repos.map((repo) => {
        const isSelected = selected.includes(repo.full_name)
        const count = planCounts[repo.full_name] ?? 0
        const hasError = errorRepos.includes(repo.full_name)

        return (
          <div
            key={repo.full_name}
            className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-muted/50"
            onClick={() => onToggle(repo.full_name)}
          >
            <Checkbox
              checked={isSelected}
              onCheckedChange={() => onToggle(repo.full_name)}
              onClick={(event) => event.stopPropagation()}
            />
            <span className="flex-1 truncate text-sm" title={repo.full_name}>
              {repo.name}
            </span>
            {hasError ? (
              <Badge variant="destructive" className="px-1 py-0 text-xs">
                Error
              </Badge>
            ) : null}
            {!hasError && count > 0 ? (
              <Badge variant="secondary" className="text-xs tabular-nums">
                {count}
              </Badge>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
