"use client"

import { useMemo, useState } from "react"
import { SearchIcon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
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
  const [query, setQuery] = useState("")

  const filtered = useMemo(() => {
    if (!query) return repos
    const q = query.toLowerCase()
    return repos.filter(
      (repo) =>
        repo.name.toLowerCase().includes(q) ||
        repo.full_name.toLowerCase().includes(q)
    )
  }, [repos, query])

  // Sort: selected first, then by name
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const aSelected = selected.includes(a.full_name) ? 0 : 1
      const bSelected = selected.includes(b.full_name) ? 0 : 1
      if (aSelected !== bSelected) return aSelected - bSelected
      return a.name.localeCompare(b.name)
    })
  }, [filtered, selected])

  const handleSelectAll = () => {
    for (const repo of filtered) {
      if (!selected.includes(repo.full_name)) {
        onToggle(repo.full_name)
      }
    }
  }

  const handleDeselectAll = () => {
    for (const repo of filtered) {
      if (selected.includes(repo.full_name)) {
        onToggle(repo.full_name)
      }
    }
  }

  const selectedInView = filtered.filter((r) =>
    selected.includes(r.full_name)
  ).length

  return (
    <div className="space-y-2">
      <p className="text-label font-medium text-muted-foreground">
        リポジトリ
        {selected.length > 0 && (
          <span className="ml-1 text-foreground">({selected.length})</span>
        )}
      </p>

      {/* Search */}
      <div className="relative">
        <SearchIcon className="pointer-events-none absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="リポジトリを検索..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-7"
        />
      </div>

      {/* Bulk actions */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="xs"
          onClick={handleSelectAll}
          disabled={selectedInView === filtered.length}
        >
          全選択
        </Button>
        <Button
          variant="ghost"
          size="xs"
          onClick={handleDeselectAll}
          disabled={selectedInView === 0}
        >
          全解除
        </Button>
        {query && (
          <span className="ml-auto text-xs text-muted-foreground">
            {filtered.length}/{repos.length}
          </span>
        )}
      </div>

      {/* Repo list */}
      <ScrollArea className="h-[calc(100svh-360px)] min-h-40">
        <div className="space-y-0.5 pr-2">
          {sorted.map((repo) => {
            const isSelected = selected.includes(repo.full_name)
            const count = planCounts[repo.full_name] ?? 0
            const hasError = errorRepos.includes(repo.full_name)

            return (
              <div
                key={repo.full_name}
                className={`flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-muted/50 ${
                  isSelected ? "bg-muted/30" : ""
                }`}
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
          {filtered.length === 0 && (
            <p className="py-4 text-center text-xs text-muted-foreground">
              該当するリポジトリがありません
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
