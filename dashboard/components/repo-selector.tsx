"use client"

import { useMemo, useState } from "react"
import {
  AlertCircleIcon,
  ChevronsUpDownIcon,
  FilterIcon,
  XIcon,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"
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
  const [open, setOpen] = useState(false)

  const sorted = useMemo(() => {
    return [...repos].sort((a, b) => {
      const aSelected = selected.includes(a.full_name) ? 0 : 1
      const bSelected = selected.includes(b.full_name) ? 0 : 1
      if (aSelected !== bSelected) return aSelected - bSelected
      return (
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      )
    })
  }, [repos, selected])

  const handleDeselectAll = () => {
    for (const repo of repos) {
      if (selected.includes(repo.full_name)) {
        onToggle(repo.full_name)
      }
    }
  }

  const errorCount = errorRepos.length
  const selectedCount = selected.length

  const triggerLabel =
    selectedCount > 0 ? `${selectedCount}件選択中` : "リポジトリを選択"

  const commandList = (
    <RepoCommandList
      repos={sorted}
      selected={selected}
      onToggle={onToggle}
      planCounts={planCounts}
      errorRepos={errorRepos}
      onDeselectAll={handleDeselectAll}
    />
  )

  return (
    <>
      {/* 展開時: ラベル + フルトリガーボタン */}
      <div className="flex flex-col gap-2 group-data-[collapsible=icon]:hidden">
        <p className="text-label font-medium text-muted-foreground">
          リポジトリ
        </p>
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger
            render={
              <Button variant="outline" className="w-full justify-between" />
            }
          >
            <span className="flex items-center gap-1.5 truncate">
              {triggerLabel}
            </span>
            <span className="flex items-center gap-1">
              {errorCount > 0 && (
                <Badge variant="destructive" className="px-1 py-0 text-xs">
                  <AlertCircleIcon data-icon="inline-start" />
                  {errorCount}
                </Badge>
              )}
              <ChevronsUpDownIcon className="opacity-50" />
            </span>
          </PopoverTrigger>
          <PopoverContent
            align="start"
            className="w-[--popover-trigger-width] p-0"
          >
            {commandList}
          </PopoverContent>
        </Popover>
      </div>

      {/* 折りたたみ時: アイコンボタンのみ */}
      <div className="hidden group-data-[collapsible=icon]:flex group-data-[collapsible=icon]:justify-center">
        <Popover>
          <PopoverTrigger
            render={
              <Button
                variant="ghost"
                className={cn(
                  "size-8 p-0",
                  errorCount > 0 && "text-destructive"
                )}
              />
            }
          >
            <FilterIcon data-icon="inline-start" />
          </PopoverTrigger>
          <PopoverContent side="right" align="start" className="w-64 p-0">
            {commandList}
          </PopoverContent>
        </Popover>
      </div>
    </>
  )
}

function RepoCommandList({
  repos,
  selected,
  onToggle,
  planCounts,
  errorRepos,
  onDeselectAll,
}: {
  repos: GitHubRepo[]
  selected: string[]
  onToggle: (fullName: string) => void
  planCounts: Record<string, number>
  errorRepos: string[]
  onDeselectAll: () => void
}) {
  return (
    <Command>
      <CommandInput placeholder="リポジトリを検索..." />
      <CommandList>
        <CommandEmpty>該当するリポジトリがありません</CommandEmpty>
        <CommandGroup>
          {repos.map((repo) => {
            const isSelected = selected.includes(repo.full_name)
            const count = planCounts[repo.full_name] ?? 0
            const hasError = errorRepos.includes(repo.full_name)

            return (
              <CommandItem
                key={repo.full_name}
                value={repo.full_name}
                onSelect={() => onToggle(repo.full_name)}
                data-checked={isSelected}
              >
                <span className="flex-1 truncate">{repo.name}</span>
                {hasError && (
                  <Badge variant="destructive" className="px-1 py-0 text-xs">
                    Error
                  </Badge>
                )}
                {!hasError && count > 0 && (
                  <Badge variant="secondary" className="text-xs tabular-nums">
                    {count}
                  </Badge>
                )}
              </CommandItem>
            )
          })}
        </CommandGroup>
      </CommandList>
      {selected.length > 0 && (
        <>
          <CommandSeparator />
          <div className="p-1">
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-center"
              onClick={onDeselectAll}
            >
              <XIcon data-icon="inline-start" />
              全解除
            </Button>
          </div>
        </>
      )}
    </Command>
  )
}
